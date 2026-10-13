# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestBaseDocumentLayout(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.din5008_layout = cls.env.ref("l10n_din5008.external_layout_din5008")
        cls.din5008_paperformat = cls.env.ref("l10n_din5008.paperformat_euro_din_a")
        cls.report_layout = cls.env["report.layout"].search([], limit=1)

    def setUp(self):
        super().setUp()
        self.company.external_report_layout_id = self.din5008_layout
        self.company.paperformat_id = self.din5008_paperformat
        self.company.l10n_din5008_config = {}
        self.layout = self.env["base.document.layout"].create(
            {"company_id": self.company.id, "report_layout_id": self.report_layout.id}
        )

    def test_din5008_config_related_to_company(self):
        config = {"marks": {"fold_marker": True, "hole_marker": False}}
        self.company.l10n_din5008_config = config
        self.assertEqual(self.layout.l10n_din5008_config, config)

    def test_din5008_config_write_to_company(self):
        config = {"page": {"margin_bottom": 55.0}}
        self.layout.l10n_din5008_config = config
        self.assertEqual(self.company.l10n_din5008_config, config)

    def test_din5008_config_field_is_related(self):
        self.assertEqual(
            self.layout._fields["l10n_din5008_config"].related,
            "company_id.l10n_din5008_config",
        )
        self.assertFalse(self.layout._fields["l10n_din5008_config"].readonly)

    def test_get_din5008_config(self):
        config = {"marks": {"fold_marker": True}}
        self.layout.l10n_din5008_config = config
        self.assertEqual(self.layout._get_din5008_config(), config)

    def test_get_din5008_config_empty(self):
        self.layout.l10n_din5008_config = False
        self.assertEqual(self.layout._get_din5008_config(), {})

    def test_get_din5008_config_value(self):
        self.layout.l10n_din5008_config = {
            "page": {"margin_bottom": 55.0},
            "marks": {"fold_marker": True},
        }
        self.assertEqual(
            self.layout._get_din5008_config_value("page", "margin_bottom"), 55.0
        )
        self.assertTrue(self.layout._get_din5008_config_value("marks", "fold_marker"))

    def test_get_din5008_config_value_default(self):
        self.layout.l10n_din5008_config = {}
        self.assertEqual(
            self.layout._get_din5008_config_value(
                "page", "margin_bottom", default=40.0
            ),
            40.0,
        )

    def test_get_din5008_config_value_invalid_path(self):
        self.layout.l10n_din5008_config = {
            "page": 10,
        }
        self.assertEqual(
            self.layout._get_din5008_config_value(
                "page", "margin_bottom", default=40.0
            ),
            40.0,
        )

    def test_get_din5008_config_value_none(self):
        self.layout.l10n_din5008_config = {"page": {"margin_bottom": None}}
        self.assertEqual(
            self.layout._get_din5008_config_value(
                "page", "margin_bottom", default=40.0
            ),
            40.0,
        )

    def test_config_modified(self):
        self.layout.l10n_din5008_config = {"marks": {"fold_marker": True}}
        self.assertTrue(self.layout.l10n_din5008_config_modified)

    def test_config_not_modified(self):
        self.layout.l10n_din5008_config = {}
        self.assertFalse(self.layout.l10n_din5008_config_modified)

    def test_din5008_preview_render(self):
        self.layout.l10n_din5008_config = {
            "marks": {"fold_marker": True, "hole_marker": True}
        }
        self.layout._compute_preview()
        self.assertTrue(
            self.layout.preview, "The document layout preview was not rendered."
        )
        self.assertIn("din5008_marks", self.layout.preview)
        self.assertIn("din5008_hole", self.layout.preview)
        self.assertIn("din5008_fold_1", self.layout.preview)
        self.assertIn("din5008_fold_2", self.layout.preview)

    def test_din5008_preview_without_markers(self):
        self.layout.l10n_din5008_config = {
            "marks": {"fold_marker": False, "hole_marker": False}
        }
        self.layout._compute_preview()
        self.assertTrue(self.layout.preview)
        self.assertNotIn("din5008_marks", self.layout.preview)

    def test_onchange_din5008_report_config(self):
        self.layout.l10n_din5008_config = {
            "page": {"margin_bottom": 55.0},
            "marks": {"fold_marker": True, "hole_marker": True},
        }
        self.layout._onchange_din5008_report_config()
        self.assertTrue(self.layout.preview)
        self.assertIn("din5008_marks", self.layout.preview)
        self.assertIn("din5008_hole", self.layout.preview)
        self.assertIn("din5008_fold_1", self.layout.preview)
        self.assertIn("din5008_fold_2", self.layout.preview)

    def test_action_reset_din5008_config(self):
        self.company.l10n_din5008_config = {
            "page": {"margin_bottom": 55.0},
            "marks": {"fold_marker": True},
        }
        result = self.layout.action_reset_din5008_config()
        self.assertTrue(result)
        self.assertFalse(self.company.l10n_din5008_config)
        self.assertFalse(self.layout.l10n_din5008_config)
