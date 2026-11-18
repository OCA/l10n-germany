# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_de_elster_hersteller_id = fields.Char(
        "ELSTER HerstellerID",
        config_parameter="l10n_de_tax_statement.elster_hersteller_id",
        help="The five digit ID ELSTER assigns to the manufacturer of the "
        "software which delivers the data.",
    )
