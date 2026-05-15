# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DatevAPIService(models.Model):
    _name = "datev.api.service"
    _description = "Service within the DATEV API"

    name = fields.Char(required=True)
    scopes = fields.Char()

    _sql_constraints = [
        ("uniq_name", "unique(name)", "API Service must be unique"),
    ]

    @api.model
    def find_service_or_create(self, name, scope=None):
        rec = self.search([("name", "=", name)], limit=1)
        if rec:
            return rec

        if scope:
            return self.create({"name": name, "scopes": scope})

        return self.browse()
