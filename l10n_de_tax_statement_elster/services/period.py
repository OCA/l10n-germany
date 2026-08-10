# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar

from odoo import _
from odoo.exceptions import UserError

PERIOD_MONTHLY = {
    1: "01",
    2: "02",
    3: "03",
    4: "04",
    5: "05",
    6: "06",
    7: "07",
    8: "08",
    9: "09",
    10: "10",
    11: "11",
    12: "12",
}

PERIOD_QUARTERLY = {
    1: "41",
    2: "42",
    3: "43",
    4: "44",
}


def get_elster_period(from_date, to_date):
    """Determine the ELSTER period code from a date range.

    Returns (period_code, 'month'|'quarter').
    Raises UserError for invalid periods.
    """
    if not from_date or not to_date:
        raise UserError(_("Der Voranmeldungszeitraum ist nicht vollständig angegeben."))

    y = from_date.year
    if y != to_date.year:
        raise UserError(
            "Ein Voranmeldungszeitraum über einen Jahreswechsel " "ist nicht zulässig."
        )

    if y != 2026:
        raise UserError(
            "Der ELSTER Export unterstützt nur das Steuerjahr 2026. "
            f"Der angegebene Zeitraum liegt in {y}."
        )

    # Monthly: single full calendar month
    if from_date.month == to_date.month:
        if from_date.day != 1:
            raise UserError(
                "Der Voranmeldungszeitraum beginnt nicht am " "ersten Tag eines Monats."
            )
        last_day = calendar.monthrange(y, from_date.month)[1]
        if to_date.day != last_day:
            raise UserError(
                "Der Voranmeldungszeitraum entspricht keinem " "vollständigen Monat."
            )
        return (PERIOD_MONTHLY[from_date.month], "month")

    # Quarterly: full quarter
    Q_MAP = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
    for q, (q_start, q_end) in Q_MAP.items():
        if from_date.month == q_start and to_date.month == q_end:
            if from_date.day != 1:
                raise UserError(
                    "Der Voranmeldungszeitraum beginnt nicht am "
                    "ersten Tag eines Quartals."
                )
            last_day = calendar.monthrange(y, q_end)[1]
            if to_date.day != last_day:
                raise UserError(
                    "Der Voranmeldungszeitraum entspricht keinem "
                    "vollständigen Quartal."
                )
            return (PERIOD_QUARTERLY[q], "quarter")

    # Full year detection (must be last to avoid matching quarters first)
    if from_date.month == 1 and to_date.month == 12:
        if from_date.day == 1 and to_date.day == 31:
            raise UserError(
                "Ein ganzes Kalenderjahr kann nicht als "
                "Umsatzsteuer-Voranmeldung exportiert werden. "
                "Verwenden Sie dafür die separate "
                "Umsatzsteuer-Jahreserklärung."
            )

    raise UserError(
        "Der Voranmeldungszeitraum konnte keinem gültigen Monat "
        "oder Quartal zugeordnet werden."
    )


def get_period_label(period_code):
    """Return human-readable label for a period code."""
    monthly_map = {v: k for k, v in PERIOD_MONTHLY.items()}
    quarterly_map = {v: k for k, v in PERIOD_QUARTERLY.items()}
    if period_code in monthly_map:
        return f"Monat {monthly_map[period_code]}/2026"
    if period_code in quarterly_map:
        q_labels = {1: "1. Quartal", 2: "2. Quartal", 3: "3. Quartal", 4: "4. Quartal"}
        return f"{q_labels[quarterly_map[period_code]]} 2026"
    return period_code
