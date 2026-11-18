# Copyright 2018 Onestein (<http://www.onestein.eu>)
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.l10n_de_tax_statement.models.elster_config import (
    HERSTELLER_ID_PARAM,
)


@tagged("-at_install", "post_install")
class TestTaxStatementZM(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test company",
                "country_id": cls.env.ref("base.de").id,
                "state_id": cls.env.ref("base.state_de_bw").id,
                "currency_id": cls.env.ref("base.EUR").id,
                "street": "Testgasse 13",
                "zip": "08151",
                "city": "Musterstadt",
            }
        )
        cls.company.l10n_de_stnr = "93815/08152"
        cls.env["ir.config_parameter"].sudo().set_param(HERSTELLER_ID_PARAM, "12345")
        cls.env.company = cls.company
        cls.env["account.chart.template"].try_loading("de_skr03", cls.company)
        cls.tax_products = cls.env.ref(f"account.{cls.company.id}_tax_eu_sale_skr03")
        cls.tax_services = cls.env.ref(f"account.{cls.company.id}_tax_free_eu_skr03")
        cls.journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "sale")], limit=1
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": cls.env.ref("base.nl").id,
                "vat": "NL000099998B57",
            }
        )
        cls.statement = cls.env["l10n.de.tax.statement"].create(
            {"year": 2025, "period": "03"}
        )

    def _create_invoice(self, products=0.0, services=0.0, partner=None):
        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice", default_journal_id=self.journal.id
            )
        )
        invoice_form.partner_id = partner or self.partner
        invoice_form.invoice_date = date(2025, 3, 15)
        for price_unit, tax in (
            (products, self.tax_products),
            (services, self.tax_services),
        ):
            if not price_unit:
                continue
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line"
                line.price_unit = price_unit
                line.tax_ids.clear()
                line.tax_ids.add(tax)
        invoice = invoice_form.save()
        invoice.action_post()
        return invoice

    def _approve(self):
        """Check the statement like its approval does, with or without
        a module which sends it"""
        self.statement.action_update()
        self.statement._check_approve()

    def test_zm(self):
        self._create_invoice(products=100.0, services=50.0)
        self.assertFalse(self.statement.zm_line_ids)
        self.statement.action_update()
        self.assertRecordValues(
            self.statement.zm_line_ids,
            [
                {
                    "partner_id": self.partner.id,
                    "country_code": "NL",
                    "vat": "NL000099998B57",
                    "amount_products": 100.0,
                    "amount_services": 50.0,
                }
            ],
        )
        self.assertEqual(
            self.statement._generate_zm_download_lines()[3:],
            [["NL000099998B57", 100, "L"], ["NL000099998B57", 50, "S"]],
        )
        self._approve()
        self.assertEqual(
            sorted(self.statement._get_approve_attachments().mapped("name")),
            ["UStVA_2025_03.xml", "ZM_2025_03.csv"],
        )

    def test_zm_create(self):
        """A new statement computes its ZM lines as well"""
        self._create_invoice(products=100.0)
        statement = self.env["l10n.de.tax.statement"].create(
            {
                "company_id": self.company.id,
                "year": 2025,
                "period": "03",
                "is_corrected": True,
            }
        )
        self.assertEqual(statement.zm_line_ids.amount_products, 100.0)

    def test_zm_changed(self):
        """The approval fails if the ZM changed since the last update"""
        self.statement.action_update()
        self._create_invoice(products=100.0)
        with self.assertRaises(UserError):
            self.statement.action_approve()

    def test_zm_wrong_country(self):
        self._create_invoice(products=100.0)
        self.partner.country_id = self.env.ref("base.de")
        # a draft shows the wrong line, its approval fails
        self.statement.action_update()
        self.assertEqual(self.statement.zm_line_ids.country_code, "DE")
        with self.assertRaises(UserError):
            self._approve()
        self.partner.country_id = self.env.ref("base.us")
        with self.assertRaises(UserError):
            self._approve()

    def test_zm_no_vat(self):
        self._create_invoice(products=100.0)
        self.partner.vat = False
        with self.assertRaises(UserError):
            self._approve()

    def test_zm_commercial_partner(self):
        contact = self.env["res.partner"].create(
            {"name": "Test contact", "parent_id": self.partner.id, "type": "delivery"}
        )
        self._create_invoice(products=100.0, partner=contact)
        self._create_invoice(products=50.0)
        self.statement.action_update()
        self.assertRecordValues(
            self.statement.zm_line_ids,
            [{"partner_id": self.partner.id, "amount_products": 150.0}],
        )
