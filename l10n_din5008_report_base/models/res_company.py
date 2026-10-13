# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_din5008_config = fields.Json(
        string="DIN 5008 Configuration",
        default=dict,
        help="Configuration for DIN 5008 reports.",
    )

    def _get_din5008_config(self):
        self.ensure_one()
        return self.l10n_din5008_config or {}

    def _get_din5008_config_value(self, *keys, default=None):
        self.ensure_one()
        value = self._get_din5008_config()

        for key in keys:
            if not isinstance(value, dict):
                return default

            value = value.get(key)

        return default if value is None else value

    def _set_din5008_config_value(self, *keys, value):
        self.ensure_one()

        if not keys:
            raise ValueError("At least one key is required.")

        config = dict(self.l10n_din5008_config or {})
        current = config

        for key in keys[:-1]:
            child = current.get(key)

            if not isinstance(child, dict):
                child = {}
                current[key] = child

            current = child

        current[keys[-1]] = value
        self.l10n_din5008_config = config
