# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.tests import tagged

from .common import EricTestSendCase


@tagged("-at_install", "post_install")
class TestEricTestSend(EricTestSendCase):
    """The statement against the test interface of ELSTER, see
    EricTestSendCase"""

    def test_approve_dialog(self):
        statement = self._create_statement()
        action = statement.action_approve()
        self.assertEqual(action["res_model"], "l10n.de.tax.statement.eric.send")
        self.env["l10n.de.tax.statement.eric.send"].with_context(
            **action["context"]
        ).create(
            {
                "certificate": base64.b64encode(self.certificate),
                "pin": self.pin,
                "privacy_notice_read": True,
            }
        ).action_send()
        # a test case doesn't declare the statement
        self.assertEqual(statement.state, "draft")
        self._assert_accepted(statement, statement._get_eric_name())

    def test_approve_stored(self):
        self._store_credentials()
        statement = self._create_statement()
        self.assertIs(statement.action_approve(), True)
        self.assertEqual(statement.state, "draft")
        self._assert_accepted(statement, statement._get_eric_name())
