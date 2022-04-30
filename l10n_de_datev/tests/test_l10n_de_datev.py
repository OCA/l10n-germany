# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import datetime
import io
import zipfile
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestL10nDeDatevExport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.range = self.env["date.range"].create(
            {
                "name": "testrange",
                "type_id": self.env.ref("account_fiscal_year.fiscalyear").id,
                "date_start": datetime.date.today(),
                "date_end": datetime.date.today(),
            }
        )
        self.wizard = self.env["l10n_de_datev.export"].create(
            {
                "fiscalyear_id": self.range.id,
                "period_ids": [(6, 0, self.range.ids)],
            }
        )
        self.env.user.company_id.write({
            'datev_consultant_id': '4242424',
            'datev_client_id': '42424',
            'datev_account_code_length': 4,
        })

    def test_validation(self):
        """ Test that we validate our input data """
        self.env.user.company_id.write({
            'datev_consultant_id': None,
        })
        with self.assertRaises(ValidationError):
            self.wizard.action_generate()

    def test_happy_flow(self):
        """ Test generation works as expected """
        self.wizard.action_generate()
        zip_buffer = io.BytesIO(base64.b64decode(self.wizard.file_data))
        self.assertTrue(zipfile.is_zipfile(zip_buffer))
        with zipfile.ZipFile(zip_buffer) as zip_file:
            files = zip_file.namelist()
            partners = "EXTF_DebKred_Stamm.csv"
            self.assertIn(partners, files)
            customer = self.env['res.partner'].search(
                [('customer', '=', True)], limit=1,
            )
            self.assertIn(
                customer.name,
                zip_file.open(partners).read().decode('utf8'),
            )
