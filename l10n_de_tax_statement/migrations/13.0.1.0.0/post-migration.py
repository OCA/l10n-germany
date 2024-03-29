# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rule = env.ref(
        "l10n_de_tax_statement.tax_statement_security_rule",
        raise_if_not_found=False,
    )
    if rule:
        domain = "['|',('company_id','=',False),('company_id','in',company_ids)]"
        rule.write({"domain_force": domain})
