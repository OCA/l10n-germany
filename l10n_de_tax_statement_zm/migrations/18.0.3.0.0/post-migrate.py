# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup

from odoo import SUPERUSER_ID, api


def _get_old_zm_lines_message(statement):
    """Return the ZM lines of the statement as a table"""
    cells = Markup("").join(
        Markup("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>")
        % (
            line.partner_id.display_name or "",
            line.vat or "",
            line.country_code or "",
            line.amount_products,
            line.amount_services,
        )
        for line in statement.zm_line_ids
    )
    return (
        Markup(
            "<p>The ZM lines of the statement before the migration:</p>"
            "<table><tr><th>Partner</th><th>VAT</th><th>Country</th>"
            "<th>Products</th><th>Services</th></tr>%s</table>"
        )
        % cells
    )


def migrate(cr, version):
    """The migration of l10n_de_tax_statement computes the drafts again
    before this module is loaded: compute their ZM lines too, the old ones
    stay in the message of the statement"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    statements = env["l10n.de.tax.statement"].search([("state", "=", "draft")])
    for statement in statements.filtered("zm_line_ids"):
        statement.message_post(body=_get_old_zm_lines_message(statement))
    statements._update_lines()
