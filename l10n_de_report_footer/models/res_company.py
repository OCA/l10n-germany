# Copyright 2026 glueckkanja AG
# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import lxml.html
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

REPORT_FOOTER_RENDER_MODEL = "res.company"
# layout texts of the company that may contain placeholders
REPORT_PLACEHOLDER_FIELDS = ("report_footer", "company_details", "report_header")


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = ["res.company", "report.layout.config.mixin"]

    # Keep the <t t-out="object.field"/> placeholders inserted by the editor
    # (tags and attributes); scripts and javascript links are still removed.
    report_footer = fields.Html(sanitize_tags=False, sanitize_attributes=False)
    company_details = fields.Html(sanitize_tags=False, sanitize_attributes=False)
    report_header = fields.Html(sanitize_tags=False, sanitize_attributes=False)
    report_layout_config = fields.Json(
        string="Report Layout Configuration",
        default=dict,
        help="Settings of the document layout (bottom margin, ...), one key "
        "per setting. See the method _get_report_layout_config_fields.",
    )

    @api.model
    def mail_allowed_qweb_expressions(self):
        """Company fields everyone may use as placeholders in the layout texts."""
        return super().mail_allowed_qweb_expressions() + (
            "object.display_name",
            "object.street",
            "object.street2",
            "object.zip",
            "object.city",
            "object.state_id.name",
            "object.country_id.name",
            "object.country_id.code",
            "object.phone",
            "object.mobile",
            "object.email",
            "object.website",
            "object.vat",
            "object.company_registry",
            "object.currency_id.name",
        )

    @api.constrains("report_layout_config")
    def _check_report_layout_config(self):
        """Check the stored settings against their declaration.

        Keys that no installed module declares are kept untouched.
        """
        for company in self:
            config = company.report_layout_config or {}
            if not isinstance(config, dict):
                raise ValidationError(
                    self.env._("The report layout configuration must be a dictionary.")
                )
            specs = company._get_report_layout_config_fields_by_key()
            for key, value in config.items():
                if key in specs:
                    company._check_report_layout_config_value(specs[key], value)

    @api.model
    def _check_report_layout_config_value(self, spec, value):
        label, field_type = spec["label"], spec["type"]
        valid = {
            "boolean": lambda v: isinstance(v, bool),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "float": lambda v: isinstance(v, int | float) and not isinstance(v, bool),
            "selection": lambda v: v
            in [option[0] for option in spec.get("options", [])],
            "char": lambda v: isinstance(v, str),
        }.get(field_type)
        if valid and not valid(value):
            raise ValidationError(
                self.env._(
                    "%(field)s has an invalid value: %(value)r.",
                    field=label,
                    value=value,
                )
            )
        if field_type not in ("integer", "float"):
            return
        if spec.get("allow_zero") and value == 0:
            return
        low, high = spec.get("min"), spec.get("max")
        if (low is not None and value < low) or (high is not None and value > high):
            raise ValidationError(
                self.env._(
                    "%(field)s must be %(zero)sbetween %(low)s and %(high)s.",
                    field=label,
                    zero=self.env._("0 or ") if spec.get("allow_zero") else "",
                    low=low,
                    high=high,
                )
            )

    @api.constrains(*REPORT_PLACEHOLDER_FIELDS)
    def _check_report_footer_placeholders(self):
        """Only template editors may store texts with advanced expressions.

        Placeholders on the usual company fields (see
        ``mail_allowed_qweb_expressions``) are allowed for everyone, other
        expressions need the template editor group, like in mail templates.
        Administrators are not restricted. The texts are rendered with
        elevated rights, so the check happens when they are written.
        """
        renderer = self.env["mail.render.mixin"]
        if not renderer._is_restricted():
            return
        for company in self:
            for field_name in REPORT_PLACEHOLDER_FIELDS:
                template = company[field_name]
                if template and renderer._has_unsafe_expression_template_qweb(
                    str(template), REPORT_FOOTER_RENDER_MODEL
                ):
                    group = self.env.ref("mail.group_mail_template_editor")
                    raise AccessError(
                        self.env._(
                            "Only members of the group %(group)s can use advanced "
                            "placeholders in %(field)s.",
                            group=group.name,
                            field=company._fields[field_name]._description_string(
                                self.env
                            ),
                        )
                    )

    @api.model
    def _apply_placeholder_overrides(self, template, overrides):
        """Replace ``<t t-out="object.<field>"/>`` nodes by the given values.

        Used by the document layout wizard to preview values that are not
        stored yet (for example a formatted sender line).
        """
        if not overrides or 't-out="object.' not in template:
            return template
        root = lxml.html.fragment_fromstring(template, create_parent="div")
        for node in root.xpath(".//*[@t-out]"):
            expression = node.get("t-out", "")
            field_name = expression.removeprefix("object.")
            if not expression.startswith("object.") or field_name not in overrides:
                continue
            value = str(overrides[field_name] or "")
            if node.tag == "t":
                # <t> is not an HTML tag: replace the node by its value
                text = value + (node.tail or "")
                previous, parent = node.getprevious(), node.getparent()
                if previous is not None:
                    previous.tail = (previous.tail or "") + text
                else:
                    parent.text = (parent.text or "") + text
                parent.remove(node)
            else:
                del node.attrib["t-out"]
                for child in list(node):
                    node.remove(child)
                node.text = value
        return (root.text or "") + "".join(
            lxml.html.tostring(child, encoding="unicode") for child in root
        )

    @api.model
    def _render_company_placeholders(self, template, company, overrides=None):
        """Render the placeholders of a layout text for ``company``.

        Placeholders are ``<t t-out="object.field"/>`` nodes as inserted by
        the dynamic placeholder picker of the HTML editor, where ``object``
        is the company. ``overrides`` maps field names to values used instead
        of the stored ones.
        """
        if not template or not company:
            return Markup("")
        template = self._apply_placeholder_overrides(str(template), overrides)
        rendered = (
            self.env["mail.render.mixin"]
            .sudo()
            ._render_template(
                str(template), REPORT_FOOTER_RENDER_MODEL, [company.id], engine="qweb"
            )
        )
        return Markup(rendered.get(company.id) or "")

    def _render_report_footer(self):
        """Footer text of the company with rendered placeholders."""
        self.ensure_one()
        return self._render_company_placeholders(self.report_footer, self)

    def _render_company_details(self):
        """Address block of the company with rendered placeholders."""
        self.ensure_one()
        return self._render_company_placeholders(self.company_details, self)

    def _render_report_header(self):
        """Tagline of the company with rendered placeholders."""
        self.ensure_one()
        return self._render_company_placeholders(self.report_header, self)
