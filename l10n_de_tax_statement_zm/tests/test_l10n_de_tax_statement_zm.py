# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestTaxStatementZM(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.eur = cls.env["res.currency"].search([("name", "=", "EUR")])
        cls.coa = cls.env.ref("l10n_de_skr03.l10n_de_chart_template", False)
        cls.coa = cls.coa or cls.env.ref("l10n_generic_coa.configurable_chart_template")
        cls.company_parent = cls.env["res.company"].create(
            {
                "name": "Parent Company",
                "country_id": cls.env.ref("base.de").id,
                "currency_id": cls.eur.id,
            }
        )
        cls.env.user.company_id = cls.company_parent
        cls.coa.try_loading()
        cls.env["l10n.de.tax.statement"].search([("state", "!=", "posted")]).unlink()

        cls.tag_1 = cls.env["account.account.tag"].create(
            {
                "name": "+81 base",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_2 = cls.env["account.account.tag"].create(
            {
                "name": "+41 base",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_3 = cls.env["account.account.tag"].create(
            {
                "name": "+81 base",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_4 = cls.env["account.account.tag"].create(
            {
                "name": "+21 base",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )

        cls.tax_1 = cls.env["account.tax"].create({"name": "Tax 1", "amount": 19})
        cls.tax_1.invoice_repartition_line_ids[0].tag_ids = cls.tag_1
        cls.tax_1.invoice_repartition_line_ids[1].tag_ids = cls.tag_2

        cls.tax_2 = cls.env["account.tax"].create({"name": "Tax 2", "amount": 7})
        cls.tax_2.invoice_repartition_line_ids[0].tag_ids = cls.tag_3
        cls.tax_2.invoice_repartition_line_ids[1].tag_ids = cls.tag_4

        cls.statement_1 = cls.env["l10n.de.tax.statement"].create(
            {"name": "Statement 1", "version": "2021"}
        )

    def _create_test_invoice(self, products=True, services=True):
        account_receivable = self.env["account.account"].create(
            {
                "account_type": "expense",
                "code": "EXPTEST",
                "name": "Test expense account",
            }
        )
        self.journal_1 = self.env["account.journal"].create(
            {
                "name": "Journal 1",
                "code": "Jou1",
                "type": "sale",
                "default_account_id": account_receivable.id,
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Test partner"})

        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
                default_journal_id=self.journal_1.id,
            ),
        )
        invoice_form.partner_id = self.partner
        self.assertEqual(self.journal_1, invoice_form.journal_id)
        invoice_form.invoice_date = fields.Date.today()
        if products:
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line 1"
                line.quantity = 1.0
                line.price_unit = 100.0
                line.tax_ids.clear()
                line.tax_ids.add(self.tax_1)
        if services:
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line 2"
                line.quantity = 1.0
                line.price_unit = 50.0
                line.tax_ids.clear()
                line.tax_ids.add(self.tax_2)

        invoice = invoice_form.save()

        if products or services:
            self.assertTrue(len(invoice.line_ids))
        else:
            self.assertFalse(len(invoice.line_ids))

        for line in invoice.invoice_line_ids:
            self.assertEqual(account_receivable, line.account_id)

        return invoice

    def test_01_post_final(self):
        self.statement_with_zm = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Statement 1",
                "version": "2021",
            }
        )

        # all previous statements must be already posted
        self.statement_with_zm.statement_update()
        with self.assertRaises(UserError):
            self.statement_with_zm.post()

        self.statement_1.statement_update()
        self.statement_1.post()
        self.assertEqual(self.statement_1.state, "posted")

        # first post
        self.statement_with_zm.post()

        self.assertEqual(self.statement_with_zm.state, "posted")
        self.assertTrue(self.statement_with_zm.date_posted)

        self.statement_with_zm.zm_update()

        # then finalize
        self.statement_with_zm.finalize()
        self.assertEqual(self.statement_with_zm.state, "final")
        self.assertTrue(self.statement_with_zm.date_posted)

        with self.assertRaises(UserError):
            self.statement_with_zm.zm_update()

    def test_02_zm_invoice(self):
        self.statement_1.post()
        self.statement_with_zm = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Statement 1",
                "version": "2021",
            }
        )

        invoice = self._create_test_invoice(services=False)
        invoice.partner_id.country_id = self.env.ref("base.be")
        invoice.action_post()

        self.statement_with_zm.zm_update()
        self.statement_with_zm.post()
        self.assertTrue(self.statement_with_zm.zm_line_ids)
        self.assertTrue(self.statement_with_zm.zm_total)

        for zm_line in self.statement_with_zm.zm_line_ids:
            self.assertTrue(zm_line.amount_products)
            self.assertFalse(zm_line.amount_services)
            amount_products = zm_line.format_amount_products
            self.assertEqual(float(amount_products), zm_line.amount_products)
            amount_services = zm_line.format_amount_services
            self.assertEqual(float(amount_services), zm_line.amount_services)

    def test_03_zm_invoice_service(self):
        self.statement_1.post()
        self.statement_with_zm = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Statement 1",
                "version": "2021",
            }
        )

        invoice = self._create_test_invoice(products=False)
        invoice.partner_id.country_id = self.env.ref("base.be")
        for invoice_line in invoice.invoice_line_ids:
            for tax_line in invoice_line.tax_ids:
                for rep_line in tax_line.invoice_repartition_line_ids:
                    rep_line.tag_ids = self.tag_4
        invoice.action_post()
        self.statement_with_zm.statement_update()

        self.statement_with_zm.post()
        self.assertTrue(self.statement_with_zm.zm_line_ids)
        self.assertTrue(self.statement_with_zm.zm_total)

        for zm_line in self.statement_with_zm.zm_line_ids:
            self.assertFalse(zm_line.amount_products)
            self.assertTrue(zm_line.amount_services)
            amount_products = zm_line.format_amount_products
            self.assertEqual(float(amount_products), zm_line.amount_products)
            amount_services = zm_line.format_amount_services
            self.assertEqual(float(amount_services), zm_line.amount_services)

    def test_04_zm_invoice_de(self):
        self.statement_1.post()
        self.statement_with_zm = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Statement 1",
                "version": "2021",
            }
        )

        invoice = self._create_test_invoice()
        invoice.partner_id.country_id = self.env.ref("base.de")
        invoice.action_post()

        with self.assertRaises(ValidationError):
            self.statement_with_zm.post()

    def test_05_zm_invoice_outside_europe(self):
        self.statement_1.post()
        self.statement_with_zm = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Statement 1",
                "version": "2021",
            }
        )

        invoice = self._create_test_invoice()
        invoice.partner_id.country_id = self.env.ref("base.us")
        invoice.action_post()

        with self.assertRaises(ValidationError):
            self.statement_with_zm.post()

    def test_06_zm_invoice_download(self):
        self.statement_1.post()
        self.statement_with_zm = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Statement 1",
                "version": "2021",
            }
        )

        invoice = self._create_test_invoice()
        invoice.partner_id.country_id = self.env.ref("base.nl")
        invoice.partner_id.vat = "NL000099998B57"
        invoice.action_post()
        self.statement_with_zm.statement_update()
        self.statement_with_zm.post()

        self.statement_with_zm.zm_download()
