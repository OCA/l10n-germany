# Copyright 2018 IT IS AG <oca@itis.de>
# Copyright 2018 Florian Kantelberg <florian.kantelberg@initos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "German Toponyms",
    "version": "14.0.1.0.1",
    "author": "IT IS AG Germany, " "initOS GmbH, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "category": "Localization",
    "depends": [
        "base_location_geonames_import",
        "l10n_de_country_states",
    ],
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "wizard/l10n_de_toponyms_wizard.xml",
    ],
    "installable": True,
}
