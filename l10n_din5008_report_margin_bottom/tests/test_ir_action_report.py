# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.addons.base.tests.common import BaseCommon


class TestIrActionsReportDin5008(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.report = cls.env["ir.actions.report"].search([], limit=1)
        cls.din5008_layout = cls.env.ref("l10n_din5008.external_layout_din5008")

    def test_margin_is_set_for_din5008_layout(self):
        self.company.external_report_layout_id = self.din5008_layout
        self.company.l10n_din5008_margin_bottom = 28

        specific_paperformat_args = {}

        with patch(
            "odoo.addons.base.models.ir_actions_report."
            "IrActionsReport._build_wkhtmltopdf_args",
            return_value=["super-args"],
        ) as super_method:
            result = self.report._build_wkhtmltopdf_args(
                paperformat_id=None,
                landscape=False,
                specific_paperformat_args=specific_paperformat_args,
            )

        self.assertEqual(result, ["super-args"])
        super_method.assert_called_once()

        forwarded_args = super_method.call_args.kwargs["specific_paperformat_args"]

        self.assertEqual(
            forwarded_args["data-report-margin-bottom"],
            28,
        )

    def test_margin_is_not_set_for_other_layout(self):
        self.company.external_report_layout_id = self.env.ref(
            "web.external_layout_standard"
        )
        self.company.l10n_din5008_margin_bottom = 28

        specific_paperformat_args = {}

        with patch(
            "odoo.addons.base.models.ir_actions_report."
            "IrActionsReport._build_wkhtmltopdf_args",
            return_value=["super-args"],
        ) as super_method:
            result = self.report._build_wkhtmltopdf_args(
                paperformat_id=None,
                landscape=False,
                specific_paperformat_args=specific_paperformat_args,
            )

        self.assertEqual(result, ["super-args"])
        super_method.assert_called_once()

        forwarded_args = super_method.call_args.kwargs["specific_paperformat_args"]

        self.assertNotIn(
            "data-report-margin-bottom",
            forwarded_args,
        )

    def test_existing_specific_paperformat_args_are_preserved(self):
        self.company.external_report_layout_id = self.din5008_layout
        self.company.l10n_din5008_margin_bottom = 35

        specific_paperformat_args = {
            "data-report-dpi": 96,
            "data-report-margin-top": 20,
        }

        with patch(
            "odoo.addons.base.models.ir_actions_report."
            "IrActionsReport._build_wkhtmltopdf_args",
            return_value=["super-args"],
        ) as super_method:
            result = self.report._build_wkhtmltopdf_args(
                paperformat_id=None,
                landscape=False,
                specific_paperformat_args=specific_paperformat_args,
            )

        self.assertEqual(result, ["super-args"])
        super_method.assert_called_once()

        forwarded_args = super_method.call_args.kwargs["specific_paperformat_args"]

        self.assertEqual(
            forwarded_args["data-report-dpi"],
            96,
        )
        self.assertEqual(
            forwarded_args["data-report-margin-top"],
            20,
        )
        self.assertEqual(
            forwarded_args["data-report-margin-bottom"],
            35,
        )

    def test_none_specific_paperformat_args(self):
        self.company.external_report_layout_id = self.din5008_layout
        self.company.l10n_din5008_margin_bottom = 28

        with patch(
            "odoo.addons.base.models.ir_actions_report."
            "IrActionsReport._build_wkhtmltopdf_args",
            return_value=["super-args"],
        ) as super_method:
            result = self.report._build_wkhtmltopdf_args(
                paperformat_id=None,
                landscape=False,
                specific_paperformat_args=None,
            )

        self.assertEqual(result, ["super-args"])
        super_method.assert_called_once()

        forwarded_args = super_method.call_args.kwargs["specific_paperformat_args"]

        self.assertEqual(
            forwarded_args["data-report-margin-bottom"],
            28,
        )

    def test_din5008_layout_not_found(self):
        self.company.external_report_layout_id = self.din5008_layout
        self.company.l10n_din5008_margin_bottom = 28

        specific_paperformat_args = {}

        with (
            patch.object(
                type(self.env),
                "ref",
                return_value=False,
            ),
            patch(
                "odoo.addons.base.models.ir_actions_report."
                "IrActionsReport._build_wkhtmltopdf_args",
                return_value=["super-args"],
            ) as super_method,
        ):
            result = self.report._build_wkhtmltopdf_args(
                paperformat_id=None,
                landscape=False,
                specific_paperformat_args=specific_paperformat_args,
            )

        self.assertEqual(result, ["super-args"])
        super_method.assert_called_once()

        forwarded_args = super_method.call_args.kwargs["specific_paperformat_args"]

        self.assertNotIn(
            "data-report-margin-bottom",
            forwarded_args,
        )
