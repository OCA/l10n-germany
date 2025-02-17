# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(
        env.cr, "l10n_de_tax_statement", "migrations/17.0.1.0.0/noupdate_changes.xml"
    )
