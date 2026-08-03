# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools.translate import LazyTranslate

_lt = LazyTranslate(__name__, default_lang="en_US")


def _tax_statement_dict_2026():
    return {
        "13": {
            "code": "13",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt("... zum Steuersatz von 19 % (81)"),
        },
        "14": {
            "code": "14",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt("... zum Steuersatz von 7 % (86)"),
        },
        "15": {
            "code": "15",
            "base": 0.0,
            "name": _lt("... zum Steuersatz von 0 % (87)"),
        },
        "16": {
            "code": "16",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt("... zu anderen Steuersätzen (35 / 36)"),
        },
        "17": {
            "code": "17",
            "base": 0.0,
            "name": _lt(
                "Lieferungen land- u. forstw. Betriebe "
                "nach § 24 UStG an Abnehmer mit USt-IdNr (77)"
            ),
        },
        "18": {
            "code": "18",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt(
                "Umsätze § 24 UStG "
                "(Sägewerke, Getränke u. alk. Flüssigkeiten) (76 / 80)"
            ),
        },
        "19": {
            "code": "19",
            "base": 0.0,
            "name": _lt(
                "Innergemeinschaftliche Lieferungen "
                "(§ 4 Nr. 1b UStG) an Abnehmer mit USt-IdNr (41)"
            ),
        },
        "20": {
            "code": "20",
            "base": 0.0,
            "name": _lt("Neue Fahrzeuge an Abnehmer ohne USt-IdNr (44)"),
        },
        "21": {
            "code": "21",
            "base": 0.0,
            "name": _lt(
                "Neue Fahrzeuge außerh. eines Unternehmens § 2a UStG (49)"
            ),
        },
        "22": {
            "code": "22",
            "base": 0.0,
            "name": _lt(
                "Weitere steuerfr. Umsätze mit Vorsteuerabzug, "
                "z.B. Ausfuhrlief., SAFE (43)"
            ),
        },
        "23": {
            "code": "23",
            "base": 0.0,
            "name": _lt(
                "Steuerfreie Umsätze ohne Vorsteuerabzug "
                "(§ 4 Nr. 8 bis 29 UStG, § 19 Abs. 1 UStG) (48)"
            ),
        },
        "24": {
            "code": "24",
            "base": 0.0,
            "name": _lt(
                "Steuerfreie innergemeinschaftliche Erwerbe "
                "(§§ 4b und 25c UStG) (91)"
            ),
        },
        "25": {
            "code": "25",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt(
                "Steuerpflichtige innergemeinschaftliche Erwerbe "
                "zum Steuersatz von 19 % (89)"
            ),
        },
        "26": {
            "code": "26",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt("... zum Steuersatz von 7 % (93)"),
        },
        "27": {
            "code": "27",
            "base": 0.0,
            "name": _lt("... zum Steuersatz von 0 % (90)"),
        },
        "28": {
            "code": "28",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt("... zu anderen Steuersätzen (95 / 98)"),
        },
        "29": {
            "code": "29",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt(
                "Neue Fahrzeuge (§ 1b Abs. 2 u. 3 UStG) "
                "von Lieferern ohne USt-IdNr (94 / 96)"
            ),
        },
        "30": {
            "code": "30",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt(
                "Sonst. Leistungen § 3a Abs. 2 UStG "
                "eines im übr. Gemeinschaftsgeb. ans. Untern. "
                "(§ 13b Abs. 1 UStG) (46 / 47)"
            ),
        },
        "31": {
            "code": "31",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt(
                "Umsätze, die unter das GrEStG fallen "
                "(§ 13b Abs. 2 Nr. 3 UStG) (73 / 74)"
            ),
        },
        "32": {
            "code": "32",
            "base": 0.0,
            "tax": 0.0,
            "name": _lt(
                "Andere Leistungen "
                "(§ 13b Abs. 2 Nr. 1, 2, 4 bis 12 UStG) (84 / 85)"
            ),
        },
        "33": {
            "code": "33",
            "base": 0.0,
            "name": _lt(
                "Lieferungen des 1. Abnehmers bei innergemeinsch. "
                "Dreiecksgeschäften (§ 25b UStG) (42)"
            ),
        },
        "34": {
            "code": "34",
            "base": 0.0,
            "name": _lt(
                "Steuerpfl. Umsätze, für die der Leistungsempfänger "
                "die Steuer nach § 13b Abs. 5 UStG schuldet (60)"
            ),
        },
        "35": {
            "code": "35",
            "base": 0.0,
            "name": _lt(
                "Nicht steuerb. sonst. Leistungen "
                "gemäß § 18b Satz 1 Nr. 2 UStG (21)"
            ),
        },
        "36": {
            "code": "36",
            "base": 0.0,
            "name": _lt(
                "Übrige nicht steuerbare Umsätze "
                "(Leistungsort nicht im Inland) (45)"
            ),
        },
        "37": {
            "code": "37",
            "tax": 0.0,
            "name": _lt(
                "Umsatzsteuer (Summe der Zeilen 13 bis 18 und 25 bis 32)"
            ),
        },
        "38": {
            "code": "38",
            "tax": 0.0,
            "name": _lt(
                "Vorsteuerbeträge aus Rechnungen von anderen "
                "Unternehmern (§ 15 Abs. 1 S. 1 Nr. 1 UStG), "
                "aus § 27 Abs. 40a UStG und aus innergemeinsch. "
                "Dreiecksgeschäften (§ 25b Abs. 5 UStG) (66)"
            ),
        },
        "39": {
            "code": "39",
            "tax": 0.0,
            "name": _lt(
                "Vorsteuerbeträge aus dem innergemeinsch. Erwerb "
                "von Gegenständen (§ 15 Abs. 1 S. 1 Nr. 3 UStG) (61)"
            ),
        },
        "40": {
            "code": "40",
            "tax": 0.0,
            "name": _lt(
                "Entstandene Einfuhrumsatzsteuer "
                "(§ 15 Abs. 1 S. 1 Nr. 2 UStG) (62)"
            ),
        },
        "41": {
            "code": "41",
            "tax": 0.0,
            "name": _lt(
                "Vorsteuerbeträge aus Leistungen i.S.d. § 13b UStG "
                "(§ 15 Abs. 1 S. 1 Nr. 4 UStG) (67)"
            ),
        },
        "42": {
            "code": "42",
            "tax": 0.0,
            "name": _lt(
                "Vorsteuerbeträge nach allg. Durchschnittssätzen "
                "berechnet (§ 23a UStG) (63)"
            ),
        },
        "43": {
            "code": "43",
            "tax": 0.0,
            "name": _lt(
                "Vorsteuerabzug für innergemeinsch. Lief. neuer Fahrz. "
                "außerh. eines Untern. (§ 2a UStG) sowie von "
                "Kleinuntern. i.S.d. § 19 Abs. 1 UStG (59)"
            ),
        },
        "44": {
            "code": "44",
            "tax": 0.0,
            "name": _lt("Berichtigung des Vorsteuerabzugs (§ 15a UStG) (64)"),
        },
        "45": {
            "code": "45",
            "tax": 0.0,
            "name": _lt(
                "Verbleibender Betrag "
                "(Zeile 37 abzüglich der Zeilen 38 bis 44)"
            ),
        },
        "46": {
            "code": "46",
            "tax": 0.0,
            "name": _lt(
                "Steuer infolge Wechsels der Besteuerungsform sowie "
                "Nachsteuer auf versteuerte Anzahlungen (65)"
            ),
        },
        "47": {
            "code": "47",
            "tax": 0.0,
            "name": _lt(
                "Unrichtig/unberechtigt ausgewiesene Steuerbeträge "
                "(§ 14c UStG) sowie § 6a Abs. 4 S. 2, "
                "§ 17 Abs. 1 S. 7, § 25b Abs. 2, "
                "§ 27 Abs. 40a UStG (69)"
            ),
        },
        "48": {
            "code": "48",
            "tax": 0.0,
            "name": _lt("Umsatzsteuer-Vorauszahlung / Überschuss (83)"),
        },
        "49": {
            "code": "49",
            "tax": 0.0,
            "name": _lt(
                "Abzug der festgesetzten Sondervorauszahlung "
                "für Dauerfristverlängerung (39)"
            ),
        },
        "50": {
            "code": "50",
            "tax": 0.0,
            "name": _lt(
                "Verbleibende Umsatzsteuer-Vorauszahlung / "
                "Verbleibender Überschuss"
            ),
        },
        "51": {
            "code": "51",
            "base": 0.0,
            "name": _lt(
                "Minderung der Bemessungsgrundlage "
                "(in den Zeilen 13 bis 18 enthalten) (50)"
            ),
        },
        "52": {
            "code": "52",
            "tax": 0.0,
            "name": _lt(
                "Minderung der abziehbaren Vorsteuerbeträge "
                "(in Zeile 38 aus Rechn. v. a. Untern. sowie "
                "Zeilen 42 u. 43 enthalten) (37)"
            ),
        },
    }


def _map_tax_code_line_code_2026():
    return {
        "81": "13",
        "86": "14",
        "87": "15",
        "35": "16",
        "36": "16",
        "77": "17",
        "76": "18",
        "80": "18",
        "41": "19",
        "44": "20",
        "49": "21",
        "43": "22",
        "48": "23",
        "91": "24",
        "89": "25",
        "93": "26",
        "90": "27",
        "95": "28",
        "98": "28",
        "94": "29",
        "96": "29",
        "46": "30",
        "47": "30",
        "73": "31",
        "74": "31",
        "84": "32",
        "85": "32",
        "42": "33",
        "60": "34",
        "21": "35",
        "45": "36",
        "66": "38",
        "61": "39",
        "62": "40",
        "67": "41",
        "63": "42",
        "59": "43",
        "64": "44",
        "65": "46",
        "69": "47",
        "50": "51",
        "37": "52",
    }


def _finalize_lines_2026(lines):
    _13b = lines["13"]["tax"]
    _14b = lines["14"]["tax"]
    _16b = lines["16"]["tax"]
    lines["18"]["tax"] = lines["18"]["base"] * 0.19
    _18b = lines["18"]["tax"]

    _25b = lines["25"]["tax"]
    _26b = lines["26"]["tax"]
    lines["28"]["tax"] = lines["28"]["tax"] * -1
    _28b = lines["28"]["tax"]
    _29b = lines["29"]["tax"]

    lines["30"]["base"] = lines["30"]["base"] * -1
    _30b = lines["30"]["tax"]
    lines["31"]["tax"] = lines["31"]["base"] * 0.19
    _31b = lines["31"]["tax"]
    lines["32"]["base"] = lines["32"]["base"] * -1
    lines["32"]["tax"] = lines["32"]["base"] * 0.19
    _32b = lines["32"]["tax"]

    _37b = (
        _13b + _14b + _16b + _18b + _25b + _26b + _28b + _29b
        + _30b + _31b + _32b
    )

    lines["38"]["tax"] = lines["38"]["tax"] * -1
    _38b = lines["38"]["tax"]
    lines["39"]["tax"] = lines["39"]["tax"] * -1
    _39b = lines["39"]["tax"]
    lines["40"]["tax"] = lines["40"]["tax"] * -1
    _40b = lines["40"]["tax"]
    lines["41"]["tax"] = lines["41"]["tax"] * -1
    _41b = lines["41"]["tax"]
    lines["42"]["tax"] = lines["42"]["tax"] * -1
    _42b = lines["42"]["tax"]
    lines["43"]["tax"] = lines["43"]["tax"] * -1
    _43b = lines["43"]["tax"]
    lines["44"]["tax"] = lines["44"]["tax"] * -1
    _44b = lines["44"]["tax"]

    _45b = _37b + _38b + _39b + _40b + _41b + _42b + _43b + _44b

    _46b = lines["46"]["tax"]
    _47b = lines["47"]["tax"]

    _48b = _45b + _46b + _47b

    _49b = lines["49"]["tax"]

    _50b = _48b - _49b

    lines["37"].update({"tax": _37b})
    lines["45"].update({"tax": _45b})
    lines["48"].update({"tax": _48b})
    lines["50"].update({"tax": _50b})

    to_be_checked = ["13", "14", "16", "18", "25", "26", "28", "29"]
    for code in to_be_checked:
        tax_sign = 1 if lines[code]["tax"] >= 0.0 else -1
        base_sign = 1 if lines[code]["base"] >= 0.0 else -1
        if tax_sign != base_sign:
            lines[code]["base"] *= -1

    return lines


def _totals_2026():
    return ["48", "49"]


def _base_display_2026():
    return (
        "13", "14", "15", "16", "17", "18",
        "19", "20", "21", "22", "23",
        "24", "25", "26", "27", "28", "29",
        "30", "31", "32",
        "33", "34", "35", "36",
        "51",
    )


def _tax_display_2026():
    return (
        "13", "14", "16", "18",
        "25", "26", "28", "29",
        "30", "31", "32",
        "37",
        "38", "39", "40", "41", "42", "43", "44",
        "45",
        "46", "47",
        "48", "49", "50",
        "52",
    )


def _group_display_2026():
    return ()


def _editable_display_2026():
    return (
        "13", "14", "15", "16", "17", "18",
        "19", "20", "21", "22", "23",
        "24", "25", "26", "27", "28", "29",
        "30", "31", "32",
        "33", "34", "35", "36",
        "46", "47", "49",
        "51", "52",
    )


def _total_display_2026():
    return (
        "37", "45", "48", "50",
    )
