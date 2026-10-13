# Copyright 2026 glueckkanja AG
# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import api, models

# optional company fields (module l10n_de) offered as footer lines
REPORT_FOOTER_OPTIONAL_FIELDS = (
    ("footer.show_de_tax_number", "l10n_de_stnr"),
    ("footer.show_de_widnr", "l10n_de_widnr"),
)


class ReportLayoutConfigMixin(models.AbstractModel):
    """Helpers for the layout settings stored in ``report_layout_config``.

    The settings of the document layout are stored in one JSON field of the
    company (a flat dictionary with dotted keys such as ``page.margin_bottom``)
    instead of one column per setting. Modules declare their settings in
    ``_get_report_layout_config_fields`` and the document layout wizard
    renders them with the ``report_layout_config`` widget.

    The report templates receive ``company`` either as a ``res.company``
    record or, in the preview of the document layout wizard, as the
    ``base.document.layout`` record itself. Both models inherit this mixin.
    """

    _name = "report.layout.config.mixin"
    _description = "Report Layout Configuration Helpers"

    def _get_report_footer_section(self):
        """Section (tab of the wizard) holding the footer settings."""
        return {
            "section": "footer",
            "section_label": self.env._("Footer"),
            "section_sequence": 50,
        }

    def _get_report_layout_config_fields(self):
        """Return the settings stored in ``report_layout_config``.

        One dictionary per setting with the keys:

        - ``key``: dotted key in the configuration, e.g. ``page.margin_bottom``
        - ``label``, ``help``: translated texts shown in the wizard
        - ``section``, ``section_label``, ``section_sequence``: tab of the wizard
        - ``type``: ``boolean``, ``integer``, ``float``, ``selection`` or ``char``
        - ``default``: value used when the key is not stored
        - ``min``, ``max``, ``step``: range of the numeric types; with
          ``allow_zero`` the value 0 is accepted outside the range
        - ``options``: ``(value, label)`` pairs of a selection
        - ``options`` on a ``char`` setting: ``(value, label)`` presets offered
          next to the free text input
        - ``validate``: name of a method of this mixin called with the
          declaration and the value when the setting is stored; it raises a
          ``ValidationError`` for invalid values
        - ``highlight``: key of the preview area outlined while the field is
          focused (``o_report_preview_highlight_<key>``)
        - ``visible_if``: ``{key: value}`` of other settings that must match
        - ``layouts``: view keys of the report layouts offering the setting
          (absent: every layout)

        Extend this method to register the settings of a module.
        """
        footer = self._get_report_footer_section()
        company_fields = self.env["res.company"]._fields
        specs = [
            {
                "key": "page.margin_bottom",
                "label": self.env._("Bottom Margin (mm)"),
                "help": self.env._(
                    "Bottom page margin reserved for the footer of PDF reports. "
                    "0 keeps the bottom margin of the paper format."
                ),
                "section": "page",
                "section_label": self.env._("Page"),
                "section_sequence": 100,
                "type": "integer",
                "default": 0,
                "min": 5,
                "max": 60,
                "allow_zero": True,
                "step": 1,
                "highlight": "footer",
            },
        ]
        for key, field_name in REPORT_FOOTER_OPTIONAL_FIELDS:
            field = company_fields.get(field_name)
            if field is None:
                continue
            label = field._description_string(self.env)
            specs.append(
                {
                    **footer,
                    "key": key,
                    "label": self.env._("Show %s", label),
                    "help": self.env._(
                        "Print the field '%s' of the company as a footer line.",
                        label,
                    ),
                    "type": "boolean",
                    "default": False,
                }
            )
        return specs

    @api.model
    def get_report_layout_config_fields(self, layout_key=None):
        """Settings offered for the report layout with the given view key."""
        return [
            spec
            for spec in self._get_report_layout_config_fields()
            if not spec.get("layouts") or layout_key in spec["layouts"]
        ]

    def _get_report_layout_config_fields_by_key(self):
        return {spec["key"]: spec for spec in self._get_report_layout_config_fields()}

    def _get_report_layout_config(self):
        self.ensure_one()
        return dict(self.report_layout_config or {})

    def _get_report_layout_config_value(self, *keys, default=None):
        """Value of a setting: stored value, ``default`` or the declared default.

        The key may be given in parts: ``("page", "margin_bottom")`` equals
        ``("page.margin_bottom",)``.
        """
        self.ensure_one()
        key = ".".join(keys)
        config = self.report_layout_config or {}
        if key in config:
            return config[key]
        if default is not None:
            return default
        spec = self._get_report_layout_config_fields_by_key().get(key)
        return spec.get("default") if spec else None

    def _set_report_layout_config_value(self, *keys, value):
        self._update_report_layout_config({".".join(keys): value})

    def _update_report_layout_config(self, values):
        """Merge ``values`` (``{dotted key: value}``) into the stored settings."""
        for record in self:
            record.report_layout_config = {
                **(record.report_layout_config or {}),
                **values,
            }

    def _get_report_footer_margin_bottom(self):
        """Bottom margin (mm) of the PDF reports, 0 for the paper format margin."""
        return int(self._get_report_layout_config_value("page.margin_bottom") or 0)

    # Footer lines

    def _get_report_footer_company(self):
        """Company record behind ``company`` of the report templates.

        The document layout wizard previews the layout of its company.
        """
        self.ensure_one()
        return self

    def _get_report_footer_company_field(self, field_name):
        """Value of a company field, False when the field does not exist."""
        company = self._get_report_footer_company()
        if field_name not in company._fields:
            return False
        return company[field_name]

    def _get_report_footer_company_field_label(self, field_name):
        """Translated label of a company field, empty when it does not exist."""
        field = self._get_report_footer_company()._fields.get(field_name)
        return field._description_string(self.env) if field else ""

    # Footer style

    def _get_report_footer_scope_class(self):
        """CSS class scoping the footer style rules of one rendered footer."""
        self.ensure_one()
        return "o_report_footer_" + re.sub(r"\W", "_", str(self.id))
