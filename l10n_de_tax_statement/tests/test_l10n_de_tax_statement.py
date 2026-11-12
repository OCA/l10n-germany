# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon

from ..models.elster_config import HERSTELLER_ID_PARAM


@tagged("-at_install", "post_install")
class TestTaxStatement(BaseCommon):
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
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.statement = cls.env["l10n.de.tax.statement"].create(
            {"year": 2025, "period": "03"}
        )

    @classmethod
    def _tax(cls, xmlid):
        return cls.env.ref(f"account.{cls.company.id}_{xmlid}")

    def _create_move(self, move_type, lines, invoice_date=date(2025, 3, 15)):
        journal = self.env["account.journal"].search(
            [
                ("company_id", "=", self.company.id),
                ("type", "=", "sale" if move_type.startswith("out") else "purchase"),
            ],
            limit=1,
        )
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type=move_type, default_journal_id=journal.id
            )
        )
        move_form.partner_id = self.partner
        move_form.invoice_date = invoice_date
        for price_unit, tax in lines:
            with move_form.invoice_line_ids.new() as line:
                line.name = "Test line"
                line.price_unit = price_unit
                line.tax_ids.clear()
                line.tax_ids.add(tax)
        move = move_form.save()
        move.action_post()
        return move

    def _get_line(self, code, statement=None):
        return (statement or self.statement).line_ids.filtered(
            lambda line: code in (line.base_code, line.tax_code)
        )

    def test_period_dates(self):
        self.assertEqual(self.statement.date_from, date(2025, 3, 1))
        self.assertEqual(self.statement.date_to, date(2025, 3, 31))
        self.statement.write({"year": 2024, "period": "02"})
        self.assertEqual(self.statement.date_to, date(2024, 2, 29))
        self.statement.period = "44"
        self.assertEqual(self.statement.date_from, date(2024, 10, 1))
        self.assertEqual(self.statement.date_to, date(2024, 12, 31))
        self.assertEqual(self.statement.name, "4th Quarter 2024")
        self.statement.is_corrected = True
        self.assertEqual(self.statement.name, "4th Quarter 2024 (corrected)")
        with self.assertRaises(ValidationError):
            self.statement.year = 25

    def test_update(self):
        self._create_move(
            "out_invoice",
            [
                (100.0, self._tax("tax_ust_19_skr03")),
                (50.0, self._tax("tax_ust_7_skr03")),
            ],
        )
        self._create_move("in_invoice", [(200.0, self._tax("tax_vst_19_skr03"))])
        # outside of the period
        self._create_move(
            "out_invoice",
            [(1000.0, self._tax("tax_ust_19_skr03"))],
            invoice_date=date(2025, 4, 1),
        )
        self.statement.action_update()
        self.assertRecordValues(
            self._get_line("81") | self._get_line("86") | self._get_line("66"),
            [
                {"base_code": "81", "tax_code": False, "base": 100.0, "tax": 19.0},
                {"base_code": "86", "tax_code": False, "base": 50.0, "tax": 3.5},
                {"base_code": False, "tax_code": "66", "base": 0.0, "tax": 38.0},
            ],
        )
        self.assertAlmostEqual(self.statement.tax_total, 19.0 + 3.5 - 38.0)
        # updating again replaces the lines
        line_count = len(self.statement.line_ids)
        self.statement.action_update()
        self.assertEqual(len(self.statement.line_ids), line_count)

    def test_other_tags(self):
        """A tax tag without a row shows up, but isn't declared"""
        tag = self.env["account.account.tag"].create(
            {
                "name": "+8111_BASE",
                "applicability": "taxes",
                "country_id": self.env.ref("base.de").id,
            }
        )
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")], limit=1
        )
        account = self.company.account_journal_suspense_account_id
        move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": date(2025, 3, 15),
                "line_ids": [
                    Command.create({"account_id": account.id, "credit": 100.0}),
                    Command.create({"account_id": account.id, "debit": 100.0}),
                ],
            }
        )
        move.line_ids.filtered("credit").tax_tag_ids = tag
        move.action_post()
        self.statement.action_update()
        line = self.statement.line_ids.filtered(lambda line: line.name == "8111_BASE")
        # signed like the tax report: a manual entry doesn't invert the tag
        self.assertEqual(line.base, -100.0)
        self.assertFalse(line.base_code)
        self.assertEqual(self.statement.tax_total, 0.0)
        self.assertEqual(line.action_view_base_items()["domain"][-1][2], tag.ids)

    def test_refund(self):
        self._create_move("out_refund", [(100.0, self._tax("tax_ust_19_skr03"))])
        self.statement.action_update()
        line = self._get_line("81")
        self.assertEqual((line.base, line.tax), (-100.0, -19.0))
        self.assertAlmostEqual(self.statement.tax_total, -19.0)

    def test_reverse_charge(self):
        """The tax owed and the input tax of § 13b UStG cancel each other out"""
        self._create_move(
            "in_invoice", [(100.0, self._tax("tax_eu_19_purchase_goods_skr03"))]
        )
        self.statement.action_update()
        line = self._get_line("46")
        self.assertEqual((line.base, line.tax), (100.0, 19.0))
        self.assertEqual(self._get_line("67").tax, 19.0)
        self.assertAlmostEqual(self.statement.tax_total, 0.0)

    def test_special_advance_payment(self):
        self._create_move("out_invoice", [(1000.0, self._tax("tax_ust_19_skr03"))])
        self.statement.action_update()
        self._get_line("39").tax = 50.0
        self.assertAlmostEqual(self.statement.tax_total, 190.0 - 50.0)

    def test_unique_period(self):
        """A period is declared once, a further statement corrects it"""
        Statement = self.env["l10n.de.tax.statement"]
        vals = {"company_id": self.company.id, "year": 2025, "period": "03"}
        with self.assertRaises(ValidationError):
            Statement.create(vals)
        corrected = Statement.create(dict(vals, is_corrected=True))
        with self.assertRaises(ValidationError):
            corrected.is_corrected = False
        # the quarter is another period
        Statement.create(dict(vals, period="41"))

    def test_corrected_statement(self):
        """A corrected statement corrects an approved statement of the period,
        or one declared outside of Odoo"""
        corrected = self.env["l10n.de.tax.statement"].create(
            {
                "company_id": self.company.id,
                "year": 2025,
                "period": "03",
                "is_corrected": True,
            }
        )
        # the statement of the period is a draft: approve it instead
        with self.assertRaisesRegex(UserError, "isn't approved yet"):
            corrected.action_approve()
        self.statement.action_approve()
        corrected.action_approve()
        self.assertEqual(corrected.corrected_statement_id, self.statement)
        # a further correction corrects the last one
        corrected_again = corrected.copy()
        corrected_again.action_approve()
        self.assertEqual(corrected_again.corrected_statement_id, corrected)
        # a period declared outside of Odoo has no statement to refer to
        outside = corrected.copy({"period": "02"})
        outside.action_approve()
        self.assertFalse(outside.corrected_statement_id)

    def test_journal_items(self):
        move = self._create_move(
            "out_invoice", [(100.0, self._tax("tax_ust_19_skr03"))]
        )
        self.statement.action_update()
        line = self._get_line("81")
        domain = line.action_view_base_items()["domain"]
        self.assertEqual(
            self.env["account.move.line"].search(domain),
            move.invoice_line_ids,
        )
        domain = line.action_view_tax_items()["domain"]
        self.assertEqual(
            self.env["account.move.line"].search(domain),
            move.line_ids.filtered("tax_line_id"),
        )

    def test_create_computes_lines(self):
        """A new statement has its lines without pressing Update"""
        self._create_move("out_invoice", [(100.0, self._tax("tax_ust_19_skr03"))])
        statement = self.env["l10n.de.tax.statement"].create(
            {
                "company_id": self.company.id,
                "year": 2025,
                "period": "03",
                "is_corrected": True,
            }
        )
        self.assertEqual(self._get_line("81", statement).base, 100.0)
        # another period computes them again
        statement.period = "04"
        self.assertEqual(self._get_line("81", statement).base, 0.0)

    def test_approve_changed_lines(self):
        """The lines the user checked must still be current on approval"""
        self._create_move("out_invoice", [(100.0, self._tax("tax_ust_19_skr03"))])
        with self.assertRaises(UserError):
            self.statement.action_approve()
        self.assertEqual(self.statement.state, "draft")
        self.statement.action_update()
        self.statement.action_approve()
        self.assertEqual(self.statement.state, "approved")

    def test_workflow(self):
        self.company.tax_lock_date = date(2025, 3, 31)
        self.statement.action_approve()
        self.assertEqual(self.statement.state, "approved")
        attachment = self.statement.message_ids.attachment_ids
        self.assertEqual(attachment.name, "UStVA_2025_03.xml")
        with self.assertRaises(UserError):
            self.statement.period = "04"
        with self.assertRaises(UserError):
            self.statement.line_ids[1].base = 1.0
        with self.assertRaises(UserError):
            self.statement.action_update()
        with self.assertRaises(UserError):
            self.statement.action_approve()
        with self.assertRaises(UserError):
            self.statement.unlink()
