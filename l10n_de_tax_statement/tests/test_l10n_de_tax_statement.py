# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestVatStatement(TransactionCase):
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
        cls.coa.try_loading(install_demo=False)
        cls.env["l10n.de.tax.statement"].search(
            [("state", "not in", ["posted", "final"])]
        ).unlink()

        cls.tag_1 = cls.env["account.account.tag"].create(
            {
                "name": "+81 base",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_2 = cls.env["account.account.tag"].create(
            {
                "name": "+81 tax",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_3 = cls.env["account.account.tag"].create(
            {
                "name": "+86 base",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_4 = cls.env["account.account.tag"].create(
            {
                "name": "+86 tax",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_5 = cls.env["account.account.tag"].create(
            {
                "name": "+41",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_6 = cls.env["account.account.tag"].create(
            {
                "name": "+62",
                "applicability": "taxes",
                "country_id": cls.env.ref("base.de").id,
            }
        )

        cls.tag_7 = cls.env["account.account.tag"].create(
            {
                "name": "46",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_8 = cls.env["account.account.tag"].create(
            {
                "name": "47",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_9 = cls.env["account.account.tag"].create(
            {
                "name": "84",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.tag_10 = cls.env["account.account.tag"].create(
            {
                "name": "85",
                "country_id": cls.env.ref("base.de").id,
            }
        )

        cls.tax_1 = cls.env["account.tax"].create({"name": "Tax 1", "amount": 19})
        cls.tax_1.invoice_repartition_line_ids[0].tag_ids = cls.tag_1
        cls.tax_1.invoice_repartition_line_ids[1].tag_ids = cls.tag_2

        cls.tax_2 = cls.env["account.tax"].create({"name": "Tax 2", "amount": 7})
        cls.tax_2.invoice_repartition_line_ids[0].tag_ids = cls.tag_3
        cls.tax_2.invoice_repartition_line_ids[1].tag_ids = cls.tag_4

        cls.tax_3 = cls.env["account.tax"].create({"name": "Tax 3", "amount": 25})
        cls.tax_3.invoice_repartition_line_ids[0].tag_ids = cls.tag_5
        cls.tax_3.invoice_repartition_line_ids[1].tag_ids = cls.tag_5

        cls.tax_4 = cls.env["account.tax"].create({"name": "Tax 4", "amount": 5})
        cls.tax_4.invoice_repartition_line_ids[0].tag_ids = cls.tag_6

        cls.tax_5 = cls.env["account.tax"].create({"name": "Tax 5", "amount": 19})
        cls.tax_5.invoice_repartition_line_ids[0].tag_ids = cls.tag_7
        cls.tax_5.invoice_repartition_line_ids[1].tag_ids = cls.tag_8

        cls.tax_6 = cls.env["account.tax"].create({"name": "Tax 6", "amount": 7})
        cls.tax_6.refund_repartition_line_ids[0].tag_ids = cls.tag_9
        cls.tax_6.refund_repartition_line_ids[1].tag_ids = cls.tag_10

        cls.statement_1 = cls.env["l10n.de.tax.statement"].create(
            {"name": "Statement 1", "version": "2018"}
        )

    def _create_test_invoice(self, additional=False, refund=False):
        account_receivable = self.env["account.account"].create(
            {
                "account_type": "expense",
                "code": "EXPTEST",
                "name": "Test expense account",
            }
        )
        journal = self.env["account.journal"].create(
            {
                "name": "Journal 1",
                "code": "Jou1",
                "type": "sale",
                "default_account_id": account_receivable.id,
            }
        )
        partner = self.env["res.partner"].create({"name": "Test partner"})

        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_refund" if refund else "out_invoice",
                default_journal_id=journal.id,
            ),
        )
        self.assertEqual(journal, invoice_form.journal_id)
        invoice_form.partner_id = partner
        invoice_form.invoice_date = fields.Date.today()
        with invoice_form.invoice_line_ids.new() as line:
            line.name = "Test line"
            line.quantity = 1.0
            line.price_unit = 100.0
            line.tax_ids.clear()
            line.tax_ids.add(self.tax_1)
        with invoice_form.invoice_line_ids.new() as line:
            line.name = "Test line"
            line.quantity = 1.0
            line.price_unit = 50.0
            line.tax_ids.clear()
            line.tax_ids.add(self.tax_2)
        if additional:
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line"
                line.quantity = 1.0
                line.price_unit = 100.0
                line.tax_ids.clear()
                line.tax_ids.add(self.tax_3)
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line"
                line.quantity = 1.0
                line.price_unit = 100.0
                line.tax_ids.clear()
                line.tax_ids.add(self.tax_4)
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line"
                line.quantity = 1.0
                line.price_unit = 100.0
                line.tax_ids.clear()
                line.tax_ids.add(self.tax_5)
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line"
                line.quantity = 1.0
                line.price_unit = 100.0
                line.tax_ids.clear()
                line.tax_ids.add(self.tax_6)
        self.invoice_1 = invoice_form.save()
        for line in self.invoice_1.invoice_line_ids:
            self.assertEqual(account_receivable, line.account_id)
        self.assertEqual(len(self.invoice_1.line_ids), 5 if not additional else 13)

    def test_01_onchange(self):
        daterange_type = self.env["date.range.type"].create({"name": "Type 1"})
        daterange = self.env["date.range"].create(
            {
                "name": "Daterange 1",
                "type_id": daterange_type.id,
                "date_start": "2016-01-01",
                "date_end": "2016-12-31",
            }
        )
        form = Form(self.statement_1)
        form.date_range_id = daterange
        statement = form.save()
        self.assertEqual(statement.from_date, datetime.date(2016, 1, 1))
        self.assertEqual(statement.to_date, datetime.date(2016, 12, 31))

        check_name = statement.company_id.name
        str_from_date = fields.Date.to_string(statement.from_date)
        str_to_date = fields.Date.to_string(statement.to_date)
        check_name += ": " + " ".join([str_from_date, str_to_date])
        self.assertEqual(statement.name, check_name)

        d_from = statement.from_date
        # by default the unreported_move_from_date is set to
        # a quarter (three months) before the from_date of the statement
        new_date = d_from + relativedelta(months=-3, day=1)
        self.assertEqual(statement.unreported_move_from_date, new_date)

        self.assertEqual(statement.tax_total, 0.0)

    def test_02_post_final(self):
        # in draft
        self.assertEqual(self.statement_1.state, "draft")
        self.statement_1.statement_update()
        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())

        # first post
        self.statement_1.statement_update()
        self.statement_1.post()
        self.assertEqual(self.statement_1.state, "posted")
        self.assertTrue(self.statement_1.date_posted)

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())

        # then finalize
        self.statement_1.finalize()
        self.assertEqual(self.statement_1.state, "final")
        self.assertTrue(self.statement_1.date_posted)

        with self.assertRaises(UserError):
            self.statement_1.write({"name": "Test Name Modified"})
        with self.assertRaises(UserError):
            self.statement_1.write({"state": "posted"})
        with self.assertRaises(UserError):
            self.statement_1.write({"date_posted": fields.Datetime.now()})
        with self.assertRaises(UserError):
            self.statement_1.unlink()
        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
            with self.assertRaises(UserError):
                line.unlink()

        self.assertEqual(self.statement_1.tax_total, 0.0)

    def test_03_reset(self):
        self.statement_1.reset()
        self.assertEqual(self.statement_1.state, "draft")
        self.assertFalse(self.statement_1.date_posted)

        self.assertEqual(self.statement_1.tax_total, 0.0)

        self.statement_1.statement_update()
        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())

    def test_04_write(self):
        self.statement_1.post()
        with self.assertRaises(UserError):
            self.statement_1.write({"name": "Test Name"})

        self.assertEqual(self.statement_1.tax_total, 0.0)

    def test_05_unlink_exception(self):
        self.statement_1.post()
        with self.assertRaises(UserError):
            self.statement_1.unlink()

    def test_06_unlink_working(self):
        self.statement_1.unlink()

    def test_07_update_exception1(self):
        self.statement_1.post()
        with self.assertRaises(UserError):
            self.statement_1.statement_update()

    def test_09_update_working(self):
        self._create_test_invoice()
        self.invoice_1.action_post()
        self.statement_1.statement_update()
        self.assertEqual(len(self.statement_1.line_ids.ids), 47)

        _25 = self.statement_1.line_ids.filtered(lambda r: r.code == "25")
        _26 = self.statement_1.line_ids.filtered(lambda r: r.code == "26")
        _27 = self.statement_1.line_ids.filtered(lambda r: r.code == "27")

        self.assertEqual(len(_25), 1)
        self.assertEqual(len(_26), 1)
        self.assertEqual(len(_27), 1)

        self.assertFalse(_25.format_base)
        self.assertFalse(_25.format_tax)
        self.assertTrue(_25.is_group)
        self.assertTrue(_25.is_readonly)
        self.assertEqual(_26.format_base, "100.00")
        self.assertFalse(_26.is_group)
        self.assertFalse(_26.is_readonly)

        self.assertEqual(_27.format_base, "50.00")
        self.assertFalse(_27.is_group)
        self.assertFalse(_27.is_readonly)

        self.assertEqual(self.statement_1.tax_total, 22.5)
        self.assertEqual(self.statement_1.format_tax_total, "22.50")

    def test_10_line_unlink_exception(self):
        self.assertEqual(len(self.statement_1.line_ids.ids), 0)
        self.assertEqual(self.statement_1.tax_total, 0.0)

        self._create_test_invoice()
        self.invoice_1.action_post()
        self.statement_1.statement_update()
        self.statement_1.post()
        with self.assertRaises(UserError):
            self.statement_1.line_ids.unlink()

        self.assertEqual(len(self.statement_1.line_ids.ids), 47)
        self.assertEqual(self.statement_1.tax_total, 22.5)

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
            self.assertTrue(line.is_readonly)
            with self.assertRaises(UserError):
                line.unlink()

    def test_12_undeclared_invoice(self):
        self._create_test_invoice()
        self.invoice_1.action_post()

        self.invoice_1.l10n_de_add_move_in_statement()
        self.assertTrue(self.invoice_1.line_ids)
        for line in self.invoice_1.line_ids:
            self.assertTrue(line.l10n_de_tax_statement_include)
        self.invoice_1.l10n_de_unlink_move_from_statement()
        self.assertTrue(self.invoice_1.line_ids)
        for line in self.invoice_1.line_ids:
            self.assertFalse(line.l10n_de_tax_statement_include)

        self.statement_1.statement_update()
        self.assertEqual(len(self.statement_1.line_ids.ids), 47)

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
        self.statement_1.post()
        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())

        invoice2 = self.invoice_1.copy()
        invoice2.date = fields.Date.today() - relativedelta(months=1)
        invoice2.invoice_date = invoice2.date
        invoice2.action_post()
        statement2 = self.env["l10n.de.tax.statement"].create(
            {"name": "Statement 2", "version": "2018"}
        )
        self.assertTrue(statement2.unreported_move_from_date)
        statement2.statement_update()
        statement2.unreported_move_from_date = fields.Date.today()
        self.assertFalse(statement2.unreported_move_ids)

        self.assertEqual(self.statement_1.tax_total, 22.5)
        self.assertEqual(self.statement_1.format_tax_total, "22.50")

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
            self.assertTrue(line.is_readonly)

    def test_13_no_previous_statement_posted(self):
        statement2 = self.env["l10n.de.tax.statement"].create(
            {"name": "Statement 2", "version": "2018"}
        )
        statement2.statement_update()
        with self.assertRaises(UserError):
            statement2.post()

        self.assertEqual(self.statement_1.tax_total, 0.0)
        self.assertEqual(self.statement_1.format_tax_total, "0.00")

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
            self.assertFalse(line.is_readonly)

    def test_14_new_version(self):
        self.assertEqual(len(self.statement_1.line_ids.ids), 0)
        self.assertEqual(self.statement_1.tax_total, 0.0)

        self._create_test_invoice()
        self.invoice_1.action_post()
        self.statement_1.version = "2019"
        self.statement_1.statement_update()
        self.statement_1.post()

        self.assertEqual(len(self.statement_1.line_ids.ids), 44)
        self.assertEqual(self.statement_1.tax_total, 22.5)

    def test_15_2021_version(self):
        self.assertEqual(len(self.statement_1.line_ids.ids), 0)
        self.assertEqual(self.statement_1.tax_total, 0.0)

        self._create_test_invoice(additional=True)
        self.invoice_1.action_post()
        self.statement_1.version = "2021"
        self.statement_1.statement_update()
        self.statement_1.post()

        self.assertEqual(len(self.statement_1.line_ids.ids), 45)
        self.assertEqual(self.statement_1.tax_total, 122.5)

    def test_16_2021_version_unreported_move_from_date_false(self):
        self.assertEqual(len(self.statement_1.line_ids.ids), 0)
        self.assertEqual(self.statement_1.tax_total, 0.0)

        self._create_test_invoice(additional=True)
        self.invoice_1.action_post()
        self.statement_1.version = "2021"
        self.statement_1.unreported_move_from_date = False
        self.statement_1.statement_update()
        self.statement_1.post()

        self.assertEqual(len(self.statement_1.line_ids.ids), 45)
        self.assertEqual(self.statement_1.tax_total, 122.5)

    def test_17_2021_version_is_invoice_basis_false(self):
        self.assertEqual(len(self.statement_1.line_ids.ids), 0)
        self.assertEqual(self.statement_1.tax_total, 0.0)

        self._create_test_invoice(additional=True)
        self.invoice_1.action_post()
        self.statement_1.version = "2021"
        self.statement_1.company_id.l10n_de_tax_invoice_basis = False
        self.statement_1.statement_update()
        self.statement_1.post()

        self.assertEqual(len(self.statement_1.line_ids.ids), 45)
        self.assertEqual(self.statement_1.tax_total, 122.5)

    def test_18_2021_version_refund(self):
        self.assertEqual(len(self.statement_1.line_ids.ids), 0)
        self.assertEqual(self.statement_1.tax_total, 0.0)

        self._create_test_invoice(additional=True, refund=True)
        self.invoice_1.action_post()
        self.statement_1.version = "2021"
        self.statement_1.company_id.l10n_de_tax_invoice_basis = False
        self.statement_1.statement_update()
        self.statement_1.post()

        self.assertEqual(len(self.statement_1.line_ids.ids), 45)
        self.assertEqual(self.statement_1.tax_total, 0.0)
