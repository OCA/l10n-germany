# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from base64 import b64encode

from odoo import exceptions
from odoo.fields import Domain
from odoo.tests import tagged
from odoo.tools.misc import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

_logger = logging.getLogger(__name__)


@tagged("post_install_l10n", "post_install", "-at_install")
class TestDatevImportCsvDtvf(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("de")
    @AccountTestInvoicingCommon.setup_chart_template("de_skr03")
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "l10n_germany_skr03",
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.analytic_plan = cls.env["account.analytic.plan"].search(
            Domain("name", "=", "Internal"), limit=1
        ) or cls.env["account.analytic.plan"].create(
            {
                "name": "Internal",
            }
        )
        for code in ("1200",):
            _logger.info(f"create account {code} for test")
            cls.env["account.account"].create(
                {
                    "name": code,
                    "code": code,
                    "account_type": "asset_receivable",
                    "reconcile": True,
                }
            )
        # cls.env["account.account"].search(
        #     [("code", "=", "4900")]
        # ).account_type = "income"
        for code in ("4811", "100", "200"):
            if cls.env["account.analytic.account"].search(
                Domain.AND(
                    [
                        Domain("code", "=", code),
                        Domain("company_id", "=", cls.env.company.id),
                    ]
                )
            ):
                continue
            _logger.info(f"create analytic.account {code} for test")
            cls.env["account.analytic.account"].create(
                {
                    "name": code,
                    "code": code,
                    "plan_id": cls.analytic_plan.id,
                }
            )

    def _test_wizard(self, filename):
        wizard = self.env["account.move.import"].create(
            {
                "file_to_import": b64encode(file_open(filename).read().encode("utf8")),
                "force_journal_id": self.env["account.journal"]
                .search([("type", "=", "sale")], limit=1)
                .id,
                "force_move_ref": "/",
                "force_move_line_name": "/",
                "post_move": True,
            }
        )
        action = wizard.run_import()
        move = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(len(move.line_ids), 196)
        first_line = move.line_ids[:1]
        self.assertEqual(first_line.account_id.code, "4900")
        self.assertEqual(first_line.credit, 0.01)
        last_line = move.line_ids[-1:]
        self.assertEqual(last_line.account_id.code, "2450")
        self.assertEqual(last_line.debit, 72)
        analytic_lines = move.line_ids.mapped("analytic_line_ids")
        self.assertEqual(len(analytic_lines), 1)
        self.assertEqual(sum(analytic_lines.mapped("amount")), 0.01)

    def test_wizard_comma_separated(self):
        self._test_wizard("datev_import_csv_dtvf/examples/datev_export.csv")

    def test_wizard_semicolon_separated(self):
        self._test_wizard("datev_import_csv_dtvf/examples/datev_export_semicolon.csv")

    def test_wizard_broken_file(self):
        wizard = self.env["account.move.import"].create(
            {
                "file_to_import": b64encode(
                    b"file,with\nwrong\ndate,format,in,third,line,,,,,wrong date"
                ),
                "force_journal_id": self.env["account.journal"]
                .search([("type", "=", "sale")], limit=1)
                .id,
                "force_move_ref": "/",
                "force_move_line_name": "/",
            }
        )
        with self.assertRaises(exceptions.UserError):
            wizard.run_import()

    def test_nonexisting_account_journal(self):
        wizard = self.env["account.move.import"].create(
            {
                "file_to_import": b64encode(
                    b"EXTF,700,22,Buchungsstapel,12,20230417083808874,,,,,12345,1234,20220101,"
                    b"4,20221201,20221231,Buchungsstapel 20220101,MM,1,,,EUR,"
                    b"\nnonexisting,accounts\n42,H,,,,,42424242,424242420,,23/01"
                ),
            }
        )
        with self.assertRaises(exceptions.UserError):
            wizard.run_import()

    def _assert_account_totals(
        self, move, account_code, expected_debit, expected_credit
    ):
        """Assert total debit and credit for all lines on a given account."""
        lines = move.line_ids.filtered(
            lambda line, code=account_code: line.account_id.code == code
        )
        self.assertAlmostEqual(
            sum(lines.mapped("debit")),
            expected_debit,
            places=2,
            msg=f"Account {account_code} total debit mismatch",
        )
        self.assertAlmostEqual(
            sum(lines.mapped("credit")),
            expected_credit,
            places=2,
            msg=f"Account {account_code} total credit mismatch",
        )

    def _import_payroll_fixture(self, apply_account_taxes=False, post=False):
        """Import the payroll fixture file and return the created move."""
        file_bytes = file_open(
            "datev_import_csv_dtvf/tests/fixtures/DTVF_payroll_test.csv", "rb"
        ).read()
        wizard = self.env["account.move.import"].create(
            {
                "file_to_import": b64encode(file_bytes),
                "force_journal_id": self.env["account.journal"]
                .search([("type", "=", "general")], limit=1)
                .id,
                "force_move_ref": "/",
                "force_move_line_name": "/",
                "post_move": post,
                "apply_account_taxes": apply_account_taxes,
            }
        )
        action = wizard.run_import()
        return self.env[action["res_model"]].browse(action["res_id"])

    def test_payroll_import_basic(self):
        """Test payroll fixture imports correctly without tax mapping."""
        move = self._import_payroll_fixture(apply_account_taxes=False)
        # 11 CSV rows x 2 move lines each = 22 lines
        self.assertEqual(len(move.line_ids), 22)
        # Move must be balanced with total 11275.00
        self.assertAlmostEqual(sum(move.line_ids.mapped("debit")), 11275.00, places=2)
        self.assertAlmostEqual(sum(move.line_ids.mapped("credit")), 11275.00, places=2)
        # Per-account debit/credit totals
        self._assert_account_totals(move, "1755", 4975.00, 5100.00)
        self._assert_account_totals(move, "4110", 2500.00, 0)
        self._assert_account_totals(move, "4120", 1500.00, 0)
        self._assert_account_totals(move, "4130", 800.00, 0)
        self._assert_account_totals(move, "8611", 0, 275.00)
        self._assert_account_totals(move, "1742", 1200.00, 1200.00)
        self._assert_account_totals(move, "1759", 0, 1200.00)

    def test_payroll_import_with_tax_mapping(self):
        """Test tax mapping applies to contra_account Automatikkonten (8611)."""
        move = self._import_payroll_fixture(apply_account_taxes=True)
        # 22 base lines + 1 merged tax line on 1776 = 23
        total_debit = sum(move.line_ids.mapped("debit"))
        total_credit = sum(move.line_ids.mapped("credit"))
        self.assertAlmostEqual(total_debit, total_credit, places=2)
        self.assertAlmostEqual(total_debit, 11275.00, places=2)
        # 8611 lines (Automatikkonto) use net amounts with tax_ids (19% VAT)
        # round_globally adjusts first (largest) row: 168.07 → 168.06
        lines_8611 = move.line_ids.filtered(
            lambda line: line.account_id.code == "8611" and line.tax_ids
        )
        self.assertEqual(len(lines_8611), 2)
        net_amounts = sorted(lines_8611.mapped(lambda line: line.debit or line.credit))
        self.assertEqual(net_amounts, [63.03, 168.06])
        # 8610 is NOT an Automatikkonto - no tax_ids
        lines_8610 = move.line_ids.filtered(lambda line: line.account_id.code == "8610")
        self.assertEqual(len(lines_8610), 1)
        self.assertFalse(lines_8610.tax_ids)
        # Odoo merges both 19% tax amounts into 1 line on account 1776
        tax_lines = move.line_ids.filtered(lambda line: line.tax_line_id)
        self.assertEqual(len(tax_lines), 1)
        self.assertEqual(tax_lines.account_id.code, "1776")
        self.assertAlmostEqual(tax_lines.credit, 43.91, places=2)
        # No auto-balancing line needed (rounding fix prevents it)
        balance_line = move.line_ids.filtered(
            lambda line: "Ausgleich" in (line.name or "")
        )
        self.assertFalse(balance_line)

    def test_payroll_import_analytic_distribution(self):
        """Test KOST1/KOST2 codes map to analytic distribution."""
        move = self._import_payroll_fixture(apply_account_taxes=False)
        analytic_100 = self.env["account.analytic.account"].search(
            Domain.AND(
                [
                    Domain("code", "=", "100"),
                    Domain("company_id", "=", self.env.company.id),
                ]
            ),
            limit=1,
        )
        analytic_200 = self.env["account.analytic.account"].search(
            Domain.AND(
                [
                    Domain("code", "=", "200"),
                    Domain("company_id", "=", self.env.company.id),
                ]
            ),
            limit=1,
        )
        # Account 4110 (expense, KOST1=100, KOST2=200) should have both
        line_4110 = move.line_ids.filtered(
            lambda line: line.account_id.code == "4110" and line.analytic_distribution
        )
        self.assertEqual(len(line_4110), 1)
        self.assertAlmostEqual(line_4110.debit, 2500.00, places=2)
        dist = line_4110.analytic_distribution
        self.assertEqual(dist[str(analytic_100.id)], 100.0)
        self.assertEqual(dist[str(analytic_200.id)], 100.0)
        # Account 4130 (expense, KOST1=100) should have analytic for 100
        line_4130 = move.line_ids.filtered(
            lambda line: line.account_id.code == "4130" and line.analytic_distribution
        )
        self.assertEqual(len(line_4130), 1)
        self.assertAlmostEqual(line_4130.debit, 800.00, places=2)
        dist_4130 = line_4130.analytic_distribution
        self.assertEqual(dist_4130[str(analytic_100.id)], 100.0)
        # Liability account 1755 should NOT get analytic distribution
        lines_1755_analytic = move.line_ids.filtered(
            lambda line: line.account_id.code == "1755" and line.analytic_distribution
        )
        self.assertFalse(
            lines_1755_analytic,
            "Liability account 1755 should not get analytic distribution",
        )
