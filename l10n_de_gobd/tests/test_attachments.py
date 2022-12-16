# Copyright 2022 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo.exceptions import AccessError
from odoo.tests.common import tagged

from odoo.addons.account.tests.account_test_savepoint import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class AttachmentCase(AccountTestInvoicingCommon):
    def setUp(self):
        super().setUp()
        self.invoice = self.init_invoice("in_invoice")
        self.attachment = self.env["ir.attachment"].create(
            {
                "res_model": "account.move",
                "res_id": self.invoice.id,
                "name": "some pdf usually",
                "datas": base64.b64encode(b"hello world"),
            }
        )

    def test_attachment_draft(self):
        """Draft moves' attachments are fully editable"""
        self.attachment.datas = base64.b64encode(b"something else")
        self.attachment.unlink()
        self.assertFalse(self.attachment.exists())

    def test_attachment_posted(self):
        """Deleting/modifying an attachment of a posted move fails"""
        self.invoice.action_post()
        with self.assertRaises(AccessError):
            self.attachment.unlink()
        with self.assertRaises(AccessError):
            self.attachment.datas = base64.b64encode(b"something else")
