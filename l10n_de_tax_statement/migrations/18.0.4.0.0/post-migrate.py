# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from markupsafe import Markup, escape

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def _get_year_period(date_from, date_to):
    """Return the year and the ELSTER period of a date range, and whether the
    range is exactly this month or quarter. Any other range gets the month of
    its start date."""
    month = f"{date_from.month:02d}"
    if date_from.day == 1:
        if date_to == date_from + relativedelta(months=1, days=-1):
            return date_from.year, month, True
        if date_from.month in (1, 4, 7, 10) and date_to == date_from + relativedelta(
            months=3, days=-1
        ):
            return date_from.year, str(41 + (date_from.month - 1) // 3), True
    return date_from.year, month, False


def _get_old_lines_message(cr, statement_id):
    """Return the lines of the old statement as a table, the old lines follow
    the line numbers of the form of their version and can't be converted"""
    cr.execute(
        """
        SELECT code, name, base, tax
          FROM l10n_de_tax_statement_line
         WHERE statement_id = %s AND (base != 0 OR tax != 0)
         ORDER BY id
        """,
        (statement_id,),
    )
    rows = cr.fetchall()
    if not rows:
        return False
    cells = Markup("").join(
        Markup("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>")
        % (code or "", escape(_get_name(name)), base or "", tax or "")
        for code, name, base, tax in rows
    )
    return (
        Markup(
            "<p>The lines of the statement before the migration:</p>"
            "<table><tr><th>Line</th><th>Name</th><th>Base</th><th>Tax</th></tr>"
            "%s</table>"
        )
        % cells
    )


def _get_name(name):
    if isinstance(name, dict):
        return name.get("en_US") or next(iter(name.values()), "")
    return name or ""


def migrate(cr, version):
    if not column_exists(cr, "l10n_de_tax_statement", "from_date"):
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(
        """
        SELECT id, company_id, from_date, to_date, state
          FROM l10n_de_tax_statement
         ORDER BY id
        """
    )
    declared = set()
    last_approved = {}
    messages = {}
    for statement_id, company_id, from_date, to_date, state in cr.fetchall():
        notes = []
        if not from_date or not to_date:
            notes.append(Markup("<p>The statement had no date range.</p>"))
            from_date = to_date = date.today()
        year, period, exact = _get_year_period(from_date, to_date)
        if not exact:
            _logger.warning(
                "Tax statement %s from %s to %s is neither a month nor a "
                "quarter, its period is set to the month of the start date.",
                statement_id,
                from_date,
                to_date,
            )
            notes.append(
                Markup(
                    "<p>The date range of the statement from %s to %s is neither "
                    "a month nor a quarter. Its period is set to the month of "
                    "the start date, please check it.</p>"
                )
                % (from_date, to_date)
            )
        # the old module had no corrected statements, any further statement
        # of a period corrects the first one
        key = (company_id, year, period)
        is_corrected = key in declared
        declared.add(key)
        # a final statement was declared, the lines of a posted one are
        # computed again and need a check
        approved = state == "final"
        # an approved corrected statement corrects the last approved one of
        # its period, like the approval sets it
        corrected_statement_id = (
            approved and is_corrected and last_approved.get(key) or None
        )
        if approved:
            last_approved[key] = statement_id
        cr.execute(
            """
            UPDATE l10n_de_tax_statement
               SET year = %s, period = %s, is_corrected = %s,
                   corrected_statement_id = %s, state = %s
             WHERE id = %s
            """,
            (
                year,
                period,
                is_corrected,
                corrected_statement_id,
                "approved" if approved else "draft",
                statement_id,
            ),
        )
        old_lines = _get_old_lines_message(cr, statement_id)
        if old_lines:
            notes.append(old_lines)
        messages[statement_id] = Markup("").join(notes)
    # the lines follow the new form: computed again for the drafts, the
    # approved statements keep the old lines in their message only
    cr.execute("DELETE FROM l10n_de_tax_statement_line")
    statements = env["l10n.de.tax.statement"].browse(list(messages))
    statements.invalidate_recordset()
    statements.modified(
        ["year", "period", "is_corrected", "corrected_statement_id", "line_ids"]
    )
    statements.flush_recordset()
    statements.filtered(lambda st: st.state == "draft")._update_lines()
    for statement in statements:
        if messages[statement.id]:
            statement.message_post(body=messages[statement.id])
