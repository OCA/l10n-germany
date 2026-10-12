# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, TransactionCase, tagged

from .common import CORE_LAYOUTS, ReportFooterCommon


@tagged("post_install", "-at_install")
class TestReportFooter(ReportFooterCommon, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_report_footer()

    def test_placeholders_kept_and_rendered(self):
        # the sanitizer keeps the placeholder nodes of the editor
        self.assertIn('t-out="object.phone"', self.company.report_footer)
        rendered = self.company._render_report_footer()
        self.assertIsInstance(rendered, Markup)
        self.assertIn("Tel. +49 30 123456 · <span>DE123456789</span>", rendered)
        self.assertIn('class="fa fa-phone"', rendered)
        self.assertNotIn("t-out", rendered)
        # default value of a placeholder when the field is empty
        self.company.phone = False
        self.assertIn("Tel. no phone", self.company._render_report_footer())
        self.company.report_footer = False
        self.assertEqual(self.company._render_report_footer(), "")

    def test_rendered_in_every_core_layout(self):
        extension = self.env["ir.ui.view"].create(
            {
                "name": "l10n_de_report_footer.test_lines",
                "type": "qweb",
                "inherit_id": self.env.ref("l10n_de_report_footer.footer_lines").id,
                "mode": "extension",
                "arch": """
                    <xpath expr="//t[@name='l10n_de_report_footer_lines']"
                           position="inside">
                        <li class="test_footer_line">Amtsgericht Berlin HRB 1</li>
                    </xpath>
                """,
            }
        )
        for layout in CORE_LAYOUTS:
            self.company.external_report_layout_id = self.env.ref(layout)
            tree = self._render_tree()
            html = self._render_html()
            self.assertIn("Tel. +49 30 123456 · <span>DE123456789</span>", html, layout)
            self.assertRegex(html, r"Acme GmbH<br/?>Musterstraße 1", layout)
            self.assertIn(f"Solutions by {self.company.name}", html, layout)
            self.assertNotIn("t-out=", html, layout)
            lines = tree.xpath(
                "//ul[@name='company_address_list']/li[@class='test_footer_line']"
            )
            self.assertEqual(len(lines), 1, layout)
        extension.unlink()

    def test_restricted_user_cannot_use_advanced_expressions(self):
        user = self.env["res.users"].create(
            {
                "name": "Footer Editor",
                "login": "footer_editor",
                "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.assertFalse(user.has_group("mail.group_mail_template_editor"))
        self.assertFalse(user.has_group("base.group_erp_manager"))
        company = self.company.with_user(user)
        # placeholders on the usual company fields are fine
        company.sudo().write(
            {
                "report_footer": (
                    '<p><t t-out="object.phone"/> <t t-out="object.vat"/></p>'
                ),
                "company_details": (
                    '<p><t t-out="object.street"/> <t t-out="object.city"/></p>'
                ),
                "report_header": '<p><t t-out="object.name"/></p>',
            }
        )
        company._check_report_footer_placeholders()
        # method calls are not, in any of the layout texts
        company.sudo().report_footer = '<p><t t-out="object.name.upper()"/></p>'
        with self.assertRaises(AccessError):
            company._check_report_footer_placeholders()
        company.sudo().report_footer = "<p>plain</p>"
        company.sudo().report_header = '<p><t t-out="object.name.upper()"/></p>'
        with self.assertRaises(AccessError):
            company._check_report_footer_placeholders()
        company.sudo().report_header = "<p>plain</p>"
        # administrators are not restricted
        self.company._check_report_footer_placeholders()

    def test_allowed_expressions_rpc(self):
        """The placeholder picker calls the whitelist on the model, like call_kw."""
        from odoo.service.model import call_kw

        expressions = call_kw(
            self.env["res.company"], "mail_allowed_qweb_expressions", [], {}
        )
        self.assertIn("object.phone", expressions)
        self.assertIn("object.partner_id.name", expressions)

    def test_placeholder_overrides(self):
        Company = self.env["res.company"]
        template = (
            '<p>Tel. <t t-out="object.phone">no phone</t> · '
            '<t t-out="object.email">no mail</t></p>'
        )
        rendered = Company._render_company_placeholders(
            template, self.company, {"phone": "+49 40 1"}
        )
        self.assertIn("Tel. +49 40 1 · info@acme.example", rendered)
        self.assertNotIn("t-out", rendered)
        # the wizard renders its own values through the overrides hook
        wizard = self.env["base.document.layout"].new(
            {"company_id": self.company.id, "report_footer": template}
        )
        self.assertIsInstance(wizard._get_company_placeholder_overrides(), dict)
        self.assertIn(
            "Tel. +49 30 123456 · info@acme.example", wizard._render_report_footer()
        )

    def test_margin_bottom(self):
        html = self._render_html(data={"report_type": "pdf"})
        self.assertNotIn("data-report-margin-bottom", html)
        self.assertNotIn("min-height: 30mm", html)
        self.assertEqual(self.company._get_report_footer_margin_bottom(), 0)
        self.company._set_report_layout_config_value("page.margin_bottom", value=30)
        self.assertEqual(self.company._get_report_footer_margin_bottom(), 30)
        html = self._render_html(data={"report_type": "pdf"})
        self.assertIn('data-report-margin-bottom="30"', html)
        self.assertNotIn("min-height: 30mm", html)
        # the HTML preview shows the margin as footer height
        tree = self._render_tree()
        footer = tree.xpath("//div[contains(@class, 'footer')]")[0]
        self.assertEqual(footer.get("style"), "min-height: 30mm;")
        args = self.report._prepare_html(html, report_model="res.partner")[4]
        self.assertEqual(args.get("data-report-margin-bottom"), "30")
        for value in (4, 61):
            with self.assertRaises(ValidationError):
                self.company.write(
                    {"report_layout_config": {"page.margin_bottom": value}}
                )
        self.company.write({"report_layout_config": {"page.margin_bottom": 0}})
        self.assertEqual(self.company._get_report_footer_margin_bottom(), 0)

    def test_report_layout_config_spec(self):
        Company = self.env["res.company"]
        spec = Company._get_report_layout_config_fields_by_key()["page.margin_bottom"]
        self.assertEqual(spec["type"], "integer")
        self.assertEqual(spec["highlight"], "footer")
        self.assertEqual(spec["section"], "page")
        # offered for every layout
        keys = [
            s["key"]
            for s in Company.get_report_layout_config_fields(
                "web.external_layout_standard"
            )
        ]
        self.assertIn("page.margin_bottom", keys)
        # declared default when the key is not stored
        self.company.report_layout_config = {}
        self.assertFalse(self.company.report_layout_config)
        self.assertEqual(self.company._get_report_layout_config(), {})
        self.assertEqual(
            self.company._get_report_layout_config_value("page.margin_bottom"), 0
        )
        self.assertEqual(
            self.company._get_report_layout_config_value("page", "margin_bottom"), 0
        )
        self.assertEqual(
            self.company._get_report_layout_config_value(
                "page.margin_bottom", default=7
            ),
            7,
        )
        self.assertIsNone(self.company._get_report_layout_config_value("unknown.key"))
        # values are merged, keys of other modules are kept
        self.company._update_report_layout_config({"other_module.flag": True})
        self.company._set_report_layout_config_value("page", "margin_bottom", value=20)
        self.assertEqual(
            self.company.report_layout_config,
            {"other_module.flag": True, "page.margin_bottom": 20},
        )
        # type checks of the declared settings
        for value in ("30", True, 30.5):
            with self.assertRaises(ValidationError):
                self.company.write(
                    {"report_layout_config": {"page.margin_bottom": value}}
                )
        with self.assertRaises(ValidationError):
            self.company.write({"report_layout_config": [1, 2]})
        self.company.report_layout_config = {}

    def test_wizard(self):
        with Form(self.env["base.document.layout"]) as wizard:
            self.assertEqual(wizard.report_footer_render_model, "res.company")
            self.assertIn(
                "Tel. +49 30 123456 · <span>DE123456789</span>", wizard.preview
            )
            self.assertNotIn("t-out=", wizard.preview)
            wizard.report_footer = '<p>Mail <t t-out="object.email">-</t></p>'
            self.assertIn("Mail info@acme.example", wizard.preview)
            wizard.report_header = '<p>Call <t t-out="object.phone"/></p>'
            self.assertIn("Call +49 30 123456", wizard.preview)
            wizard.company_details = '<p>VAT <t t-out="object.vat"/></p>'
            self.assertIn("VAT DE123456789", wizard.preview)
            # the settings offered for the selected layout
            keys = [spec["key"] for spec in wizard.report_layout_config_fields]
            self.assertIn("page.margin_bottom", keys)
            self.assertNotIn("min-height: 30mm", wizard.preview)
            wizard.report_layout_config = {
                **(wizard.report_layout_config or {}),
                "page.margin_bottom": 30,
            }
            self.assertIn("min-height: 30mm", wizard.preview)
        self.assertEqual(
            self.company._get_report_layout_config_value("page.margin_bottom"), 30
        )
        self.assertIn('t-out="object.email"', self.company.report_footer)
        with self.assertRaises(ValidationError):
            with Form(self.env["base.document.layout"]) as wizard:
                wizard.report_layout_config = {"page.margin_bottom": 70}
