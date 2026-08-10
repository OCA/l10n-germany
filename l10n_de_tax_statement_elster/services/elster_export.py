# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
ELSTER XML export service for Mein ELSTER form data upload.

Official reference:
https://www.elster.de/eportal/helpGlobal?themaGlobal=ustva_upload

The upload format is the standalone <Anmeldungssteuern> element
(not the full ElsterXML envelope with TransferHeader/NutzdatenHeader).

Schema namespace: http://finkonsens.de/elster/elsteranmeldung/ustva/v2026
Schema version: 2026
Character encoding: ISO-8859-15

Null value policy:
    Optional Kz elements with a numeric value of zero (0 or 0.00)
    are omitted from the XML output.  This avoids unnecessary
    plausibility warnings in Mein ELSTER.  Only Kz66 is always
    exported when its value is non‑zero.  Kz83 (verbleibender
    Betrag) is NOT exported because Mein ELSTER calculates it
    automatically.

    The current data model does not distinguish between
    auto‑calculated and manually entered zero values.  Normal
    auto‑calculated zeros are simply omitted.
"""

import logging
import re
from datetime import date

from lxml import etree

from .period import get_elster_period
from .tax_number import validate_tax_number

NAMESPACE_USTVA = "http://finkonsens.de/elster/elsteranmeldung/ustva/v2026"
SCHEMA_VERSION = "2026"
_logger = logging.getLogger(__name__)


def generate_elster_xml(statement):
    """Generate the Mein ELSTER upload XML.

    Returns bytes in ISO-8859-15 encoding.
    """
    period_code, _period_type = get_elster_period(
        statement.from_date, statement.to_date
    )

    tax_number = validate_tax_number(statement.company_id)
    company = statement.company_id

    root = etree.Element(
        "Anmeldungssteuern",
        nsmap={None: NAMESPACE_USTVA},
        version=SCHEMA_VERSION,
    )

    _build_datenlieferant(root, company)
    _add_element(root, "Erstellungsdatum", _format_date_elster())
    _build_steuerfall(root, statement, company, period_code, tax_number)

    xml_decl = '<?xml version="1.0" encoding="ISO-8859-15" standalone="no"?>\n'
    return xml_decl.encode("iso-8859-15") + etree.tostring(
        root, encoding="iso-8859-15", xml_declaration=False, pretty_print=True
    )


def _build_datenlieferant(parent, company):
    """Build the DatenLieferant section with company info.

    DatenLieferant/Strasse holds the full street address including
    house number because the ELSTER schema expects a single string
    here.  Do NOT split street/house number in this section.
    """
    dl = etree.SubElement(parent, "DatenLieferant")

    name = company.name or ""
    _add_element(dl, "Name", name)

    street = (company.street or "").strip()
    street2 = (company.street2 or "").strip()
    full_street = f"{street} {street2}".strip()
    _add_element(dl, "Strasse", full_street if full_street else street)
    _add_element(dl, "PLZ", company.zip or "")
    _add_element(dl, "Ort", company.city or "")
    _add_element(dl, "Telefon", company.phone or "")

    email = (company.email or "").strip()
    if email:
        _add_element(dl, "Email", email)


def _build_steuerfall(parent, statement, company, period_code, tax_number):
    """Build the Steuerfall section with UStVA data."""
    sf = etree.SubElement(parent, "Steuerfall")

    # Unternehmer section
    untern = etree.SubElement(sf, "Unternehmer")
    _add_element(untern, "Bezeichnung", company.name or "")
    street_name, house_number = _split_street(company.street)
    _add_element(untern, "Str", street_name)
    _add_element(untern, "Hausnummer", house_number)
    _add_element(untern, "Ort", company.city or "")
    _add_element(untern, "PLZ", company.zip or "")

    # Umsatzsteuervoranmeldung section
    uva = etree.SubElement(sf, "Umsatzsteuervoranmeldung")
    _add_element(uva, "Jahr", "2026")
    _add_element(uva, "Zeitraum", period_code)
    _add_element(uva, "Steuernummer", tax_number)

    _build_kennzahlen(uva, statement)


def _build_kennzahlen(uva, statement):
    """Export Kz* values from the statement lines.

    Tax bases (Bemessungsgrundlagen) are exported in full euros
    (no decimals).  Tax amounts (Steuerbetraege) are exported in
    cents with comma decimal.

    Optional Kz elements with a value of 0 or 0.00 are omitted.
    Kz83 is never auto‑exported (ELSTER calculates it).
    """
    for line in statement.line_ids.sorted("code"):
        code = line.code
        if line.is_total or line.is_group:
            continue

        has_base = line.format_base is not False
        has_tax = line.format_tax is not False

        rules = _get_line_rules()
        if code not in rules:
            continue

        rule = rules[code]
        if rule["has_base"] and has_base:
            _add_kz_value(uva, rule["kz_base"], line.base, "base")
        if rule["has_tax"] and has_tax:
            _add_kz_value(uva, rule["kz_tax"], line.tax, "tax")


def _get_line_rules():
    """Return the mapping from statement line codes to ELSTER Kz elements.

    Each line has:
    - kz_base: Kz element for Bemessungsgrundlage
    - kz_tax: Kz element for Steuerbetrag
    - has_base/has_tax: whether this Kz has base/tax columns

    ELSTER convention:
    - Tax bases: full euros, no decimals
    - Tax amounts: cent amounts, comma decimal separator

    Kz83 (verbleibender Betrag) is intentionally absent — it is
    calculated automatically by Mein ELSTER and must not appear
    in the upload XML.
    """
    return {
        "13": {"kz_base": "Kz81", "kz_tax": None, "has_base": True, "has_tax": False},
        "14": {"kz_base": "Kz86", "kz_tax": None, "has_base": True, "has_tax": False},
        "15": {"kz_base": "Kz87", "kz_tax": None, "has_base": True, "has_tax": False},
        "16": {"kz_base": "Kz35", "kz_tax": "Kz36", "has_base": True, "has_tax": True},
        "17": {"kz_base": "Kz77", "kz_tax": None, "has_base": True, "has_tax": False},
        "18": {"kz_base": "Kz76", "kz_tax": "Kz80", "has_base": True, "has_tax": True},
        "19": {"kz_base": "Kz41", "kz_tax": None, "has_base": True, "has_tax": False},
        "20": {"kz_base": "Kz44", "kz_tax": None, "has_base": True, "has_tax": False},
        "21": {"kz_base": "Kz49", "kz_tax": None, "has_base": True, "has_tax": False},
        "22": {"kz_base": "Kz43", "kz_tax": None, "has_base": True, "has_tax": False},
        "23": {"kz_base": "Kz48", "kz_tax": None, "has_base": True, "has_tax": False},
        "24": {"kz_base": "Kz91", "kz_tax": None, "has_base": True, "has_tax": False},
        "25": {"kz_base": "Kz89", "kz_tax": None, "has_base": True, "has_tax": False},
        "26": {"kz_base": "Kz93", "kz_tax": None, "has_base": True, "has_tax": False},
        "27": {"kz_base": "Kz90", "kz_tax": None, "has_base": True, "has_tax": False},
        "28": {"kz_base": "Kz95", "kz_tax": "Kz98", "has_base": True, "has_tax": True},
        "29": {"kz_base": "Kz94", "kz_tax": "Kz96", "has_base": True, "has_tax": True},
        "30": {"kz_base": "Kz46", "kz_tax": "Kz47", "has_base": True, "has_tax": True},
        "31": {"kz_base": "Kz73", "kz_tax": "Kz74", "has_base": True, "has_tax": True},
        "32": {"kz_base": "Kz84", "kz_tax": "Kz85", "has_base": True, "has_tax": True},
        "33": {"kz_base": "Kz42", "kz_tax": None, "has_base": True, "has_tax": False},
        "34": {"kz_base": "Kz60", "kz_tax": None, "has_base": True, "has_tax": False},
        "35": {"kz_base": "Kz21", "kz_tax": None, "has_base": True, "has_tax": False},
        "36": {"kz_base": "Kz45", "kz_tax": None, "has_base": True, "has_tax": False},
        "38": {"kz_base": None, "kz_tax": "Kz66", "has_base": False, "has_tax": True},
        "39": {"kz_base": None, "kz_tax": "Kz61", "has_base": False, "has_tax": True},
        "40": {"kz_base": None, "kz_tax": "Kz62", "has_base": False, "has_tax": True},
        "41": {"kz_base": None, "kz_tax": "Kz67", "has_base": False, "has_tax": True},
        "42": {"kz_base": None, "kz_tax": "Kz63", "has_base": False, "has_tax": True},
        "43": {"kz_base": None, "kz_tax": "Kz59", "has_base": False, "has_tax": True},
        "44": {"kz_base": None, "kz_tax": "Kz64", "has_base": False, "has_tax": True},
        "46": {"kz_base": None, "kz_tax": "Kz65", "has_base": False, "has_tax": True},
        "47": {"kz_base": None, "kz_tax": "Kz69", "has_base": False, "has_tax": True},
        "51": {"kz_base": "Kz50", "kz_tax": None, "has_base": True, "has_tax": False},
        "52": {"kz_base": None, "kz_tax": "Kz37", "has_base": False, "has_tax": True},
    }


def _add_element(parent, name, text):
    """Add a simple text element (only when text is not empty)."""
    if text is None or text == "":
        return None
    elem = etree.SubElement(parent, name)
    elem.text = str(text)
    return elem


def _add_kz_value(parent, name, value, value_type):
    """Add a Kz element with proper value formatting.

    - 'base': full euros, no decimals
    - 'tax': cents with period decimal, 2 places

    Optional Kz elements with a numeric value of zero are omitted
    to avoid unnecessary ELSTER plausibility warnings.  The current
    data model cannot distinguish auto‑calculated from manually
    entered zeros — normal calculated zeros are simply skipped.
    """
    if value is None:
        return None
    numeric = float(value)
    if numeric == 0.0:
        return None
    elem = etree.SubElement(parent, name)
    if value_type == "base":
        elem.text = str(int(round(numeric, 0)))
    else:
        cents_value = round(numeric, 2)
        if cents_value == int(cents_value):
            elem.text = f"{int(cents_value)}.00"
        else:
            elem.text = f"{cents_value:.2f}"
    return elem


def _format_date_elster():
    """Format current date as YYYYMMDD (ELSTER Format)."""
    return date.today().strftime("%Y%m%d")


def _split_street(street):
    """Split a street address into (street_name, house_number).

    Handles common German address formats:
        Musterstraße 8        → ("Musterstraße", "8")
        Musterstraße 8a       → ("Musterstraße", "8a")
        Musterstraße 8 A      → ("Musterstraße", "8 A")
        Musterstraße 8-10     → ("Musterstraße", "8-10")
        Musterstraße 8/10     → ("Musterstraße", "8/10")

    If the address cannot be reliably split, the entire string is
    placed in the street_name and house_number remains empty to
    avoid generating a possibly incorrect value.
    """
    if not street:
        return ("", "")
    street = street.strip()

    match = re.match(
        r"^(.+?)\s+(\d+\s*[a-zA-Z]?\s*(?:[-/]\s*\d+\s*[a-zA-Z]?)?)\s*$",
        street,
    )
    if match:
        return (match.group(1).strip(), match.group(2).strip())

    return (street, "")


def _extract_housenumber(street):
    """Return the house number portion of a street address."""
    return _split_street(street)[1]


def generate_export_filename(statement):
    """Generate a filename for the export."""
    company_name = statement.company_id.name
    safe_name = _sanitize_filename(company_name) or "firma"

    try:
        period_code, _ = get_elster_period(statement.from_date, statement.to_date)
    except Exception:
        period_code = "unknown"

    if len(period_code) == 2 and period_code.isdigit():
        return f"ustva_2026_{period_code}_{safe_name}.xml"
    elif period_code.startswith("4"):
        return f"ustva_2026_q{period_code[1]}_{safe_name}.xml"
    return f"ustva_2026_{safe_name}.xml"


def _sanitize_filename(name):
    """Clean a string for use in filenames."""
    name = str(name) if name else ""
    name = name.lower()
    name = name.replace(" ", "_").replace("ä", "ae").replace("ö", "oe")
    name = name.replace("ü", "ue").replace("ß", "ss")
    name = re.sub(r"[^a-z0-9_\-.]", "", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    if len(name) > 50:
        name = name[:50]
    return name
