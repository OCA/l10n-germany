# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import datetime
import io
import unittest
import zipfile

from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase, can_import


class TestDatevExportDtvf(TransactionCase):
    def setUp(self):
        super().setUp()
        self.range = self.env["date.range"].create(
            {
                "name": "testrange",
                "type_id": self.env["date.range.type"]
                .create(
                    {
                        "name": "testtype",
                    }
                )
                .id,
                "date_start": datetime.date.today(),
                "date_end": datetime.date.today(),
            }
        )
        with Form(self.env["datev_export_dtvf.export"]) as WizardForm:
            WizardForm.fiscalyear_id = self.range
            WizardForm.period_ids.add(self.range)
            self.wizard = WizardForm.save()
        self.env.user.company_id.write(
            {
                "datev_consultant_number": "4242424",
                "datev_client_number": "42424",
                "datev_account_code_length": 4,
            }
        )
        self.journal = self.env["account.journal"].create(
            {
                "name": "Testjournal",
                "type": "sale",
                "code": "DTV",
            }
        )
        self.account1 = self.env["account.account"].create(
            {
                "name": "Revenue",
                "code": "424242",
                "user_type_id": self.env.ref("account.data_account_type_revenue").id,
            }
        )
        self.account2 = self.env["account.account"].create(
            {
                "name": "Receivable",
                "code": "424243",
                "user_type_id": self.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
            }
        )
        self.customer = self.env["res.partner"].search(
            [("is_company", "=", True)],
            limit=1,
        )
        self.move = self.env["account.move"].create(
            {
                "journal_id": self.journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account1.id,
                            "credit": 42,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account2.id,
                            "debit": 42,
                            "partner_id": self.customer.id,
                        },
                    ),
                ],
            }
        )

    def test_validation(self):
        """Test that we validate our input data"""
        self.env.user.company_id.write(
            {
                "datev_consultant_number": None,
            }
        )
        with self.assertRaises(ValidationError):
            self.wizard.action_generate()

    def test_happy_flow(self):
        """Test generation works as expected"""
        self.wizard.name = "Hello World"
        self.move.action_post()
        self.wizard.action_generate()
        self.assertEqual(self.wizard.file_name, "Hello_World.zip")
        zip_buffer = io.BytesIO(base64.b64decode(self.wizard.file_data))
        self.assertTrue(zipfile.is_zipfile(zip_buffer))
        with zipfile.ZipFile(zip_buffer) as zip_file:
            files = zip_file.namelist()
            partners = "EXTF_DebKred_Stamm.csv"
            self.assertIn(partners, files)
            self.assertIn(
                self.customer.name,
                zip_file.open(partners).read().decode("utf8"),
            )
        self.wizard.action_draft()
        self.assertEqual(self.wizard.state, "draft")

    def test_nonautomatic_flag(self):
        """Test setting BU-Schlussel 40 works as it should"""
        self.account2.datev_export_nonautomatic = True
        self.move.action_post()
        self.wizard.journal_ids = self.journal
        self.wizard.action_generate()
        zip_buffer = io.BytesIO(base64.b64decode(self.wizard.file_data))
        with zipfile.ZipFile(zip_buffer) as zip_file:
            move_line_file_name = [
                f for f in zip_file.namelist() if f.startswith("EXTF_Buchungsstapel")
            ][0]
            with zip_file.open(move_line_file_name) as move_line_file:
                move_line = move_line_file.readlines()[2].decode("utf8")
                self.assertIn('"40"', move_line)

    def test_move_line_without_account(self):
        """Test that non-accounting (display_type!=False) lines don't crash the export"""
        self.move.write(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "display_type": "line_note",
                            "name": "This should not crash the export",
                        },
                    )
                ],
            }
        )
        self.move.action_post()
        self.wizard.action_generate()

    def test_sequence(self):
        """Test datev_partner_numbering = sequence"""
        self.wizard.company_id.datev_partner_numbering = "sequence"
        self.wizard.company_id.datev_customer_sequence_id = self.env[
            "ir.sequence"
        ].create(
            {
                "name": "DATEV customer sequence",
            }
        )
        self.wizard.company_id.datev_supplier_sequence_id = self.env[
            "ir.sequence"
        ].create(
            {
                "name": "DATEV supplier sequence",
            }
        )
        self.move.line_ids.write({"partner_id": self.customer.id})
        self.assertFalse(self.customer.l10n_de_datev_export_identifier_customer)
        self.assertFalse(self.customer.l10n_de_datev_export_identifier_supplier)
        self.move.action_post()
        self.wizard.action_generate()
        self.assertTrue(self.customer.l10n_de_datev_export_identifier_customer)

    @unittest.skipUnless(
        can_import("odoo.addons.l10n_de_datev_reports"),
        "l10n_de_datev_reports is not installed, not testing it",
    )
    def test_ee(self):
        """Test datev_partner_numbering = ee"""
        self.wizard.company_id.datev_partner_numbering = "ee"
        self.move.line_ids.write({"partner_id": self.customer.id})
        self.customer.l10n_de_datev_identifier_customer = "424242"
        self.move.action_post()
        self.wizard.action_generate()
