# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestBaseDocumentLayout(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.din5008_layout = cls.env.ref(
            "l10n_din5008.external_layout_din5008",
        )
        cls.din5008_paperformat = cls.env.ref(
            "l10n_din5008.paperformat_euro_din_a",
        )
        cls.report_layout = cls.env["report.layout"].search(
            [],
            limit=1,
        )

    def setUp(self):
        super().setUp()
        self.company.external_report_layout_id = self.din5008_layout
        self.company.paperformat_id = self.din5008_paperformat
        self.layout = self.env["base.document.layout"].create(
            {
                "company_id": self.company.id,
                "report_layout_id": self.report_layout.id,
            }
        )

    def test_din5008_marker_fields_related_to_company(self):
        self.company.l10n_din5008_hole_marker = True
        self.company.l10n_din5008_fold_marker = False
        self.assertTrue(
            self.layout.l10n_din5008_hole_marker,
        )
        self.assertFalse(
            self.layout.l10n_din5008_fold_marker,
        )

    def test_din5008_marker_fields_write_to_company(self):
        self.layout.write(
            {
                "l10n_din5008_hole_marker": False,
                "l10n_din5008_fold_marker": True,
            }
        )
        self.assertFalse(
            self.company.l10n_din5008_hole_marker,
        )
        self.assertTrue(
            self.company.l10n_din5008_fold_marker,
        )

    def test_din5008_marker_fields_are_related(self):
        fields = self.layout._fields
        self.assertEqual(
            fields["l10n_din5008_hole_marker"].related,
            "company_id.l10n_din5008_hole_marker",
        )
        self.assertEqual(
            fields["l10n_din5008_fold_marker"].related,
            "company_id.l10n_din5008_fold_marker",
        )

    def test_din5008_preview_render(self):
        self.company.l10n_din5008_hole_marker = True
        self.company.l10n_din5008_fold_marker = True
        self.layout._compute_preview()
        self.assertTrue(
            self.layout.preview,
            "The document layout preview was not rendered.",
        )
        self.assertIn("din5008_marks", self.layout.preview)
        self.assertIn("din5008_hole", self.layout.preview)
        self.assertIn("din5008_fold_1", self.layout.preview)
        self.assertIn("din5008_fold_2", self.layout.preview)

    def test_din5008_preview_without_markers(self):
        self.company.l10n_din5008_hole_marker = False
        self.company.l10n_din5008_fold_marker = False
        self.layout._compute_preview()
        self.assertTrue(
            self.layout.preview,
            "The document layout preview was not rendered.",
        )
        self.assertNotIn("din5008_marks", self.layout.preview)

    def test_din5008_preview_hole_marker_only(self):
        self.company.l10n_din5008_hole_marker = True
        self.company.l10n_din5008_fold_marker = False
        self.layout._compute_preview()
        self.assertTrue(
            self.layout.preview,
            "The document layout preview was not rendered.",
        )
        self.assertIn("din5008_marks", self.layout.preview)
        self.assertIn("din5008_hole", self.layout.preview)
        self.assertNotIn("din5008_fold_1", self.layout.preview)
        self.assertNotIn("din5008_fold_2", self.layout.preview)

    def test_onchange_din5008_report_marks(self):
        self.layout.paperformat_id = self.din5008_paperformat
        self.layout.l10n_din5008_hole_marker = True
        self.layout.l10n_din5008_fold_marker = True
        self.layout._onchange_din5008_report_marks()
        self.assertTrue(
            self.layout.preview,
            "The document layout preview was not rendered.",
        )
        self.assertIn("din5008_marks", self.layout.preview)
