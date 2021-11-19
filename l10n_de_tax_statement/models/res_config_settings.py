# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_de_tax_invoice_basis = fields.Boolean(
        string="DE Tax Invoice Basis",
        related="company_id.l10n_de_tax_invoice_basis",
    )
