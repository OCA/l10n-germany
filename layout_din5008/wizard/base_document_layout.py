# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models

from ..models.layout_din5008_mixin import DIN5008_LAYOUT_KEYS, DIN5008_PAPERFORMATS


class BaseDocumentLayout(models.TransientModel):
    """The DIN 5008 settings are edited through ``report_layout_config``.

    The settings declared in ``report_layout_config_mixin.py`` are offered by
    the widget of the base module for the DIN 5008 layouts; the wizard only
    selects the paper format and previews the sender line.
    """

    _name = "base.document.layout"
    _inherit = ["base.document.layout", "layout.din5008.mixin"]

    @api.onchange("report_layout_id")
    def _onchange_report_layout_id(self):
        res = super()._onchange_report_layout_id()
        for wizard in self:
            form = DIN5008_LAYOUT_KEYS.get(wizard.report_layout_id.view_id.key)
            if not form:
                continue
            paperformat = self.env.ref(
                DIN5008_PAPERFORMATS[form], raise_if_not_found=False
            )
            if paperformat:
                wizard.paperformat_id = paperformat
        return res

    def _get_company_placeholder_overrides(self):
        """Preview the sender line text with the unsaved wizard settings."""
        overrides = super()._get_company_placeholder_overrides()
        overrides["layout_din5008_sender_line_text"] = (
            self._layout_din5008_format_sender_line()
        )
        return overrides
