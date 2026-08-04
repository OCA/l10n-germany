# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _
from odoo.exceptions import UserError

_STATE_SCHEMA = {
    "DE-NI": {
        "prefix": "23",
        "input_pattern": r"^(\d{1,2})/(\d{1,3})/(\d{1,5})$",
    },
}


def convert_german_tax_number_to_elster(stnr, state_code=None):
    """Convert a German Steuernummer to the 13-digit ELSTER format.

    Handles two input forms:
    1. Already 13 digits (no separators) → return as-is
    2. Structured FF/BBB/UUUUP format with slashes → convert per
       Bundesland-specific schema

    The state_code (e.g. 'DE-NI') determines the Bundesland prefix
    and conversion schema. For Niedersachsen:
        FF/BBB/UUUUP  →  23FF0BBBUUUUP

    Does NOT modify the stored Steuernummer field.
    """
    stnr = (stnr or "").strip()

    if not stnr:
        raise UserError(
            _("Für den ELSTER Export fehlt die Steuernummer " "des Unternehmens.")
        )

    if re.match(r"^\d{13}$", stnr):
        return stnr

    if "/" in stnr:
        state_code_str = state_code or "ohne"
        schema = _STATE_SCHEMA.get(state_code) if state_code else None
        if not schema:
            raise UserError(
                _(
                    "Die Steuernummer '%s' enthält Schrägstriche, "
                    "aber für das Bundesland (%s) ist kein "
                    "Konvertierungsschema definiert."
                )
                % (stnr, state_code_str)
            )
        match = re.match(schema["input_pattern"], stnr)
        if not match:
            raise UserError(
                _(
                    "Die Steuernummer '%s' entspricht nicht dem "
                    "erwarteten Format FF/BBB/UUUUP.\n\n"
                    "Bitte hinterlegen Sie die Steuernummer in "
                    "Einstellungen → Unternehmen → Rechtliches "
                    "im Format XX/XXX/XXXXX."
                )
                % stnr
            )
        groups = match.groups()
        result = (
            f"{schema['prefix']}{groups[0].zfill(2)}0"
            f"{groups[1].zfill(3)}{groups[2].zfill(5)}"
        )
    else:
        digits = re.sub(r"\D", "", stnr)
        if len(digits) < 13:
            digits = digits.zfill(13)
        if not re.match(r"^\d{13}$", digits):
            raise UserError(
                _(
                    "Die Steuernummer '%s' konnte nicht in "
                    "das 13-stellige ELSTER-Format "
                    "umgewandelt werden."
                )
                % stnr
            )
        result = digits

    if not re.match(r"^\d{13}$", result):
        raise UserError(
            _(
                "Die umgewandelte Steuernummer '%s' → "
                "'%s' ist keine 13-stellige Ziffernfolge."
            )
            % (stnr, result)
        )

    return result


def validate_tax_number(company):
    """Validate and return ELSTER-formatted tax number (13 digits).

    Reads 'l10n_de_stnr' from company, converts to the 13-digit
    ELSTER format using Bundesland-specific schema. Does NOT modify
    the stored Steuernummer field (it remains untouched on invoices).
    """
    stnr = getattr(company, "l10n_de_stnr", None)
    state_code = company.state_id.code if company.state_id else None
    return convert_german_tax_number_to_elster(stnr, state_code)
