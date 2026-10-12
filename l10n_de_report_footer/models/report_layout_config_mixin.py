# Copyright 2026 glueckkanja AG
# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


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
        - ``highlight``: key of the preview area outlined while the field is
          focused (``o_report_preview_highlight_<key>``)
        - ``visible_if``: ``{key: value}`` of other settings that must match
        - ``layouts``: view keys of the report layouts offering the setting
          (absent: every layout)

        Extend this method to register the settings of a module.
        """
        return [
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
            }
        ]

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
