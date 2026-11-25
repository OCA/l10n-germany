# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import lxml.etree
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
        self.assertIn("Tel. +49 30 123456 · <span>DE123456788</span>", rendered)
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
            self.assertIn("Tel. +49 30 123456 · <span>DE123456788</span>", html, layout)
            self.assertRegex(html, r"Acme GmbH<br/?>Musterstraße 1", layout)
            self.assertIn(f"Solutions by {self.company.name}", html, layout)
            self.assertNotIn("t-out=", html, layout)
            lines = tree.xpath(
                "//ul[@name='company_address_list']/li[@class='test_footer_line']"
            )
            self.assertEqual(len(lines), 1, layout)
            # the texts carry the classes of the preview highlight
            for css_class, text in (
                ("o_report_footer_text", "Tel. +49 30 123456"),
                ("o_report_company_details", "Musterstraße 1"),
                ("o_report_tagline", "Solutions by"),
            ):
                nodes = tree.xpath(f"//*[contains(@class, '{css_class}')]")
                self.assertEqual(len(nodes), 1, f"{layout} {css_class}")
                self.assertIn(text, nodes[0].text_content(), f"{layout} {css_class}")
        extension.unlink()

    def test_preview_highlight_fields(self):
        """The layout texts of the wizard set the highlight key of the preview."""
        arch = self.env["base.document.layout"].get_view(view_type="form")["arch"]
        tree = lxml.etree.fromstring(arch)
        for field, key in (
            ("report_footer", "footer_text"),
            ("company_details", "company_details"),
            ("report_header", "tagline"),
        ):
            node = tree.xpath(f"//field[@name='{field}']")[0]
            self.assertIn(f"o_report_preview_highlight_{key}", node.get("class"))

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
                "Tel. +49 30 123456 · <span>DE123456788</span>", wizard.preview
            )
            self.assertNotIn("t-out=", wizard.preview)
            wizard.report_footer = '<p>Mail <t t-out="object.email">-</t></p>'
            self.assertIn("Mail info@acme.example", wizard.preview)
            wizard.report_header = '<p>Call <t t-out="object.phone"/></p>'
            self.assertIn("Call +49 30 123456", wizard.preview)
            wizard.company_details = '<p>VAT <t t-out="object.vat"/></p>'
            self.assertIn("VAT DE123456788", wizard.preview)
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

    def test_footer_specs(self):
        Company = self.env["res.company"]
        specs = Company._get_report_layout_config_fields_by_key()
        # the tax numbers of l10n_de are offered when the module is installed
        for key, field_name in (
            ("footer.show_de_tax_number", "l10n_de_stnr"),
            ("footer.show_de_widnr", "l10n_de_widnr"),
        ):
            if field_name not in Company._fields:
                self.assertNotIn(key, specs)
                continue
            self.assertIn(key, specs)
            self.assertEqual(specs[key]["section"], "footer")
            self.assertEqual(specs[key]["section_label"], "Footer")
            self.assertIs(specs[key]["default"], False)
            self.assertNotIn("layouts", specs[key])
            self.assertIn(
                Company._fields[field_name]._description_string(self.env),
                specs[key]["label"],
            )
            self.assertIs(self.company._get_report_layout_config_value(key), False)
            with self.assertRaises(ValidationError):
                self.company._set_report_layout_config_value(key, value=1)

    def test_footer_lines(self):
        Company = self.env["res.company"]
        if "l10n_de_stnr" not in Company._fields:
            self.skipTest("l10n_de is not installed")
        # the tax number is validated against the state of the company
        self.company.partner_id.write(
            {
                "country_id": self.env.ref("base.de").id,
                "state_id": self.env.ref("base.state_de_by").id,
            }
        )
        self.company.write(
            {"l10n_de_stnr": "9181081508155", "l10n_de_widnr": "DE123456788-00001"}
        )
        tree = self._render_tree()
        self.assertFalse(tree.xpath("//li[@name='de_tax_number']"))
        self.assertFalse(tree.xpath("//li[@name='de_widnr']"))
        self.company._update_report_layout_config(
            {"footer.show_de_tax_number": True, "footer.show_de_widnr": True}
        )
        tree = self._render_tree()
        address_list = tree.xpath("//ul[@name='company_address_list']")[0]
        tax_number = address_list.xpath("./li[@name='de_tax_number']")[0]
        label = Company._fields["l10n_de_stnr"]._description_string(self.env)
        self.assertEqual(
            " ".join(tax_number.text_content().split()), f"{label}: 9181081508155"
        )
        widnr = address_list.xpath("./li[@name='de_widnr']")[0]
        self.assertIn("DE123456788-00001", widnr.text_content())
        # the wizard previews the lines of its company
        with Form(self.env["base.document.layout"]) as wizard:
            keys = [spec["key"] for spec in wizard.report_layout_config_fields]
            self.assertIn("footer.show_de_widnr", keys)
            self.assertIn("DE123456788-00001", wizard.preview)
            wizard.report_layout_config = {
                **(wizard.report_layout_config or {}),
                "footer.show_de_widnr": False,
            }
            self.assertNotIn("DE123456788-00001", wizard.preview)
        self.assertIs(
            self.company._get_report_layout_config_value("footer.show_de_widnr"),
            False,
        )

    def test_company_field_helpers(self):
        self.company.company_registry = "HRB 1"
        self.assertEqual(
            self.company._get_report_footer_company_field("company_registry"), "HRB 1"
        )
        self.assertIs(self.company._get_report_footer_company_field("no_field"), False)
        self.assertEqual(
            self.company._get_report_footer_company_field_label("company_registry"),
            self.company._fields["company_registry"]._description_string(self.env),
        )
        self.assertEqual(self.company._get_report_footer_company_field_label("x"), "")
        wizard = self.env["base.document.layout"].new({"company_id": self.company.id})
        self.assertEqual(wizard._get_report_footer_company(), self.company)
        self.assertEqual(
            wizard._get_report_footer_company_field("company_registry"), "HRB 1"
        )
        self.assertEqual(
            self.company._get_report_footer_scope_class(),
            f"o_report_footer_{self.company.id}",
        )
