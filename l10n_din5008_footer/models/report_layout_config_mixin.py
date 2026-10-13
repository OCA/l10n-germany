# Copyright 2026 glueckkanja AG
# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo import models
from odoo.exceptions import ValidationError

DIN5008_LAYOUT_KEY = "l10n_din5008.external_layout_din5008"
# columns of the footer table of the layout: company address, footer text,
# tax numbers, bank accounts
DIN5008_FOOTER_COLUMNS = 4


class ReportLayoutConfigMixin(models.AbstractModel):
    _inherit = "report.layout.config.mixin"

    def _get_report_layout_config_fields(self):
        """Footer settings of the DIN 5008 layout shipped with Odoo."""
        footer = {**self._get_report_footer_section(), "layouts": [DIN5008_LAYOUT_KEY]}
        return super()._get_report_layout_config_fields() + [
            {
                **footer,
                "key": "footer.bank_acc_holder",
                "label": self.env._("Show Bank Account Holder"),
                "help": self.env._(
                    "Print the account holder below the name of the bank for "
                    "every bank account printed in the footer."
                ),
                "type": "boolean",
                "default": False,
                "highlight": "footer",
            },
            {
                **footer,
                "key": "footer.table_width_pattern",
                "label": self.env._("Column Widths (%)"),
                "help": self.env._(
                    "Widths of the four columns of the footer table (company "
                    "address, footer text, tax numbers, bank accounts) in percent, "
                    "separated by commas, for example '25,35,20,20'. The values "
                    "must add up to 100. Empty keeps the widths of the layout."
                ),
                "type": "char",
                "default": "",
                "validate": "_validate_din5008_footer_table_widths",
                "highlight": "footer",
            },
        ]

    def _parse_din5008_footer_table_widths(self, value):
        """Column widths (%) parsed from a pattern, None when empty or invalid."""
        if not value or not str(value).strip():
            return None
        try:
            widths = [float(part.strip()) for part in str(value).split(",")]
        except ValueError:
            return None
        if (
            len(widths) != DIN5008_FOOTER_COLUMNS
            or any(width <= 0 for width in widths)
            or abs(sum(widths) - 100) > 0.001
        ):
            return None
        return widths

    def _validate_din5008_footer_table_widths(self, spec, value):
        if (
            value
            and str(value).strip()
            and self._parse_din5008_footer_table_widths(value) is None
        ):
            raise ValidationError(
                self.env._(
                    "%(field)s must contain %(count)s positive values separated by "
                    "commas whose sum is 100, for example '25,35,20,20'.",
                    field=spec["label"],
                    count=DIN5008_FOOTER_COLUMNS,
                )
            )

    def _get_din5008_footer_table_widths(self):
        """Configured column widths (%) of the footer table, None for the layout."""
        self.ensure_one()
        return self._parse_din5008_footer_table_widths(
            self._get_report_layout_config_value("footer.table_width_pattern")
        )

    def _render_din5008_footer_css(self):
        """CSS rules applying the column widths to the footer table of the layout.

        Printed in a ``<style>`` element inside the footer, which wkhtmltopdf
        renders as a separate document. Empty without configured widths.
        """
        self.ensure_one()
        widths = self._get_din5008_footer_table_widths()
        if not widths:
            return Markup("")
        scope = self._get_report_footer_scope_class()
        table = f".{scope}.footer .company_details table"
        return Markup("\n").join(
            Markup(f"{table} td:nth-child({index}) {{ width: {width:g}%; }}")
            for index, width in enumerate(widths, 1)
        )
