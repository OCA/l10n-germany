from odoo.addons.base.tests.common import BaseCommon


class TestBaseDocumentLayout(BaseCommon):
    def test_get_din5008_optional_field(self):
        layout = self.env["base.document.layout"].create(
            {"company_id": self.env.company.id}
        )
        self.assertEqual(
            layout._get_din5008_optional_field("name"), self.env.company.name
        )

    def test_get_din5008_optional_field_missing(self):
        layout = self.env["base.document.layout"].create(
            {"company_id": self.env.company.id}
        )
        self.assertFalse(layout._get_din5008_optional_field("non_existing_field"))
