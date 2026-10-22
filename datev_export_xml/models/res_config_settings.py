# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2019 sewisoft (sewisoft.de)
# Copyright (C) 2010-2023 big-consulting GmbH (www.openbig.de)
# Copyright (C) 2010 OpenGLOBE Grzegorz Grzelak (www.openglobe.pl)
# @author Guenter Selbert <guenter.selbert@sewisoft.de>
# @author Thorsten Vocks
# @author Grzegorz Grzelak
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    datev_default_period = fields.Selection(
        related="company_id.datev_default_period",
        readonly=False,
    )

    datev_export_state = fields.Boolean(
        related="company_id.datev_export_state",
        readonly=False,
    )

    datev_vendor_order_ref = fields.Selection(
        related="company_id.datev_vendor_order_ref",
        readonly=False,
    )

    datev_customer_order_ref = fields.Selection(
        related="company_id.datev_customer_order_ref",
        readonly=False,
    )

    datev_package_limit = fields.Integer(
        related="company_id.datev_package_limit",
        readonly=False,
    )
