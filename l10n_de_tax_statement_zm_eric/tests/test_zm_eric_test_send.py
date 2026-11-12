# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged

from odoo.addons.l10n_de_tax_statement_eric.tests.common import EricTestSendCase


@tagged("-at_install", "post_install")
class TestZmEricTestSend(EricTestSendCase):
    """The statement with its ZM against the test interface of ELSTER, see
    EricTestSendCase"""

    def _create_invoice(self, partner):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "sale")], limit=1
        )
        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice", default_journal_id=journal.id
            )
        )
        invoice_form.partner_id = partner
        invoice_form.invoice_date = self.period_date
        for price_unit, xmlid in (
            (1000.0, "tax_eu_sale_skr03"),
            (250.0, "tax_free_eu_skr03"),
            (500.0, "tax_ust_19_skr03"),
        ):
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line"
                line.price_unit = price_unit
                line.tax_ids.clear()
                line.tax_ids.add(self.env.ref(f"account.{self.company.id}_{xmlid}"))
        invoice_form.save().action_post()

    def test_approve(self):
        for name, country, vat in (
            ("Test partner PL", "base.pl", "PL5630292567"),
            ("Test partner DK", "base.dk", "DK12345674"),
        ):
            self._create_invoice(
                self.env["res.partner"].create(
                    {"name": name, "country_id": self.env.ref(country).id, "vat": vat}
                )
            )
        self._store_credentials()
        statement = self._create_statement()
        self.assertEqual(len(statement._get_zm_rows()), 4)
        statement.action_approve()
        self.assertEqual(statement.state, "draft")
        self.assertFalse(statement.zm_eric_error)
        self._assert_accepted(statement, statement._get_eric_name())
        self._assert_accepted(statement, statement._get_zm_eric_name())
