# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from base64 import b64encode

from odoo import exceptions
from odoo.tests import TransactionCase
from odoo.tools.misc import file_open


class TestDatevImportCsvDtvf(TransactionCase):
    def setUp(self):
        super().setUp()
        for code in (
            "0731",
            "0980",
            "0996",
            "1200",
            "1202",
            "1240",
            "1360",
            "1500",
            "1590",
            "1610",
            "1740",
            "1750",
            "1780",
            "1789",
            "1790",
            "2712",
            "2735",
            "4110",
            "4138",
            "4160",
            "4167",
            "4360",
            "4510",
            "4520",
            "4580",
            "4650",
            "4651",
            "4900",
            "4930",
            "8125",
            "8200",
            "8339",
            "8977",
            "0965",
            "0974",
            "1200",
            "1502",
            "1503",
            "1545",
            "1576",
            "1588",
            "1700",
            "1741",
            "2114",
            "2150",
            "2450",
            "2709",
            "3425",
            "3435",
            "4120",
            "4170",
            "4653",
            "4654",
            "4655",
            "4663",
            "4666",
            "7095",
            "8605",
        ):
            if self.env["account.account"].search(
                [
                    ("code", "=", code),
                    ("company_id", "=", self.env.company.id),
                ]
            ):
                continue
            self.env["account.account"].create(
                {
                    "name": code,
                    "code": code,
                    "account_type": "asset_receivable",
                    "reconcile": True,
                }
            )
        self.env["account.account"].search([("code", "=", "7095")]).code = "7095000"
        self.env["account.account"].search([("code", "=", "1700")]).code = "170"
        self.env["account.account"].search(
            [("code", "=", "4900")]
        ).account_type = "income"
        for code in ("4811",):
            if self.env["account.analytic.account"].search(
                [
                    ("code", "=", code),
                    ("company_id", "=", self.env.company.id),
                ]
            ):
                continue
            self.env["account.analytic.account"].create(
                {
                    "name": code,
                    "code": code,
                    "plan_id": self.env.ref("analytic.analytic_plan_internal").id,
                }
            )

    def test_wizard(self):
        wizard = self.env["account.move.import"].create(
            {
                "file_to_import": b64encode(
                    file_open("datev_import_csv_dtvf/examples/datev_export.csv")
                    .read()
                    .encode("utf8")
                ),
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
