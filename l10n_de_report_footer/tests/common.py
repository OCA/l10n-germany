# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import lxml.html
from markupsafe import Markup

TEST_REPORT_ARCH = """
<t t-name="l10n_de_report_footer.test_report">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="o">
            <t t-call="web.external_layout">
                <t t-set="o" t-value="o" />
                <t t-set="address">
                    <address class="mb-0">Max Mustermann<br/>10115 Berlin</address>
                </t>
                <div class="page">
                    <t t-set="layout_document_title">
                        <span>Test Document</span>
                    </t>
                    <p>Body</p>
                </div>
            </t>
        </t>
    </t>
</t>
"""

FOOTER_WITH_PLACEHOLDERS = Markup(
    '<p>Tel. <t t-out="object.phone">no phone</t> · '
    '<span t-out="object.vat">no vat</span> <i class="fa fa-phone"/></p>'
)

CORE_LAYOUTS = [
    "web.external_layout_standard",
    "web.external_layout_boxed",
    "web.external_layout_bold",
    "web.external_layout_striped",
    "web.external_layout_folder",
    "web.external_layout_wave",
    "web.external_layout_bubble",
]


class ReportFooterCommon:
    @classmethod
    def _setup_report_footer(cls):
        cls.company = cls.env.company
        cls.company.write(
            {
                "phone": "+49 30 123456",
                "email": "info@acme.example",
                "vat": "DE123456788",
                "report_footer": FOOTER_WITH_PLACEHOLDERS,
                "company_details": Markup(
                    '<p>Acme GmbH<br/><t t-out="object.street">no street</t></p>'
                ),
                "report_header": Markup(
                    '<p>Solutions by <t t-out="object.name">nobody</t></p>'
                ),
                "street": "Musterstraße 1",
                "report_layout_config": {},
                "external_report_layout_id": cls.env.ref(
                    "web.external_layout_standard"
                ).id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Max Mustermann"})
        cls.env["ir.ui.view"].create(
            {
                "type": "qweb",
                "name": "l10n_de_report_footer.test_report",
                "key": "l10n_de_report_footer.test_report",
                "arch": TEST_REPORT_ARCH,
            }
        )
        cls.report = cls.env["ir.actions.report"].create(
            {
                "name": "Report footer test report",
                "report_name": "l10n_de_report_footer.test_report",
                "model": "res.partner",
                "report_type": "qweb-pdf",
            }
        )

    def _render_html(self, data=None):
        html = self.env["ir.actions.report"]._render_qweb_html(
            self.report, self.partner.ids, data=data
        )[0]
        if isinstance(html, bytes):
            html = html.decode("utf-8")
        return str(html)

    def _render_tree(self, data=None):
        return lxml.html.fromstring(self._render_html(data=data))
