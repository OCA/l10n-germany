# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2019 sewisoft (sewisoft.de)
# Copyright (C) 2010-2023 big-consulting GmbH (www.openbig.de)
# Copyright (C) 2010 OpenGLOBE Grzegorz Grzelak (www.openglobe.pl)
# @author Guenter Selbert <guenter.selbert@sewisoft.de>
# @author Thorsten Vocks
# @author Grzegorz Grzelak
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    datev_default_period = fields.Selection(
        [
            ("day", _("Day")),
            ("week", _("Week")),
            ("month", _("Month")),
            ("year", _("Year")),
        ],
        help="Used to get default values for start and stop date at DATEV Export!",
        default="week",
    )

    datev_export_state = fields.Boolean(
        string="Datev Export State",
        help="If set, the invoices are marked as exported when finishing a Datev export.",
    )

    datev_vendor_order_ref = fields.Selection(
        [
            ("odoo", _("Odoo Reference")),
            ("partner", _("Partner Reference")),
            ("payment", _("Payment Reference")),
        ],
        string="Vendor Order Reference",
        default="odoo",
        required=True,
    )

    datev_customer_order_ref = fields.Selection(
        [
            ("odoo", _("Odoo Reference")),
            ("partner", _("Partner Reference")),
            ("payment", _("Payment Reference")),
        ],
        string="Customer Order Reference",
        default="odoo",
        required=True,
    )

    datev_package_limit = fields.Integer(
        string="Package Limit in MB",
        default=100,
    )

    _sql_constraints = [
        (
            "check_package_limit",
            # DATEV only allows 465 MB and we leave some space
            "CHECK(datev_package_limit >= 20 AND datev_package_limit <= 400)",
            _("Package Limit for DATEV must be between 20MB and 400MB"),
        )
    ]
