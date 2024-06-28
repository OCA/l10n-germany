# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2019 sewisoft (sewisoft.de)
# Copyright (C) 2010-2023 big-consulting GmbH (www.openbig.de)
# Copyright (C) 2010 OpenGLOBE Grzegorz Grzelak (www.openglobe.pl)
# @author Guenter Selbert <guenter.selbert@sewisoft.de>
# @author Thorsten Vocks <thorsten.vocks@openbig.org>
# @author Grzegorz Grzelak
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Datev Export XML",
    "version": "14.0.1.1.4",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Guenter Selbert, Thorsten Vocks, Maciej Wichowski, Daniela Scarpa, "
    "Maria Sparenberg, initOS GmbH, Odoo Community Association (OCA)",
    "summary": "Export invoices and refunds as xml and pdf files zipped in DATEV format.",
    "website": "https://github.com/OCA/l10n-germany",
    "depends": [
        "datev_export",
    ],
    "data": [
        "data/ir_cron_data.xml",
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/account_invoice_view.xml",
        "views/datev_export_views.xml",
        "views/res_config_settings_views.xml",
        "views/templates.xml",
    ],
    "demo": [
        "demo/export_data.xml",
    ],
    "installable": True,
}
