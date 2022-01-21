# Copyright 2020 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _


def _tax_statement_dict_2021():
    return {
        "17": {"code": "17", "name": _("Anmeldung der Umsatzsteuer Vorauszahlung")},
        "18": {
            "code": "18",
            "name": _("Lief. u. sonst. Leistg. einschl. unentg. Wertabg."),
        },
        "19": {
            "code": "19",
            "name": _(
                "Steuerpflichtige Umsätze "
                "(Lief. u. sonst. Leistg. einschl. unentg. Wertabg.)"
            ),
        },
        "20": {
            "code": "20",
            "base": 0.0,
            "tax": 0.0,
            "name": _("... zum Steuersatz von 19 % (81)"),
        },
        "21": {
            "code": "21",
            "base": 0.0,
            "tax": 0.0,
            "name": _("... zum Steuersatz von 7% (86)"),
        },
        "22": {
            "code": "22",
            "base": 0.0,
            "tax": 0.0,
            "name": _("... zu anderen Steuersätzen (35 / 36)"),
        },
        "23": {
            "code": "23",
            "base": 0.0,
            "name": _(
                "Lieferungen land- u. forstw. Betriebe "
                "nach § 24 UStG an Abnehmer mit Ust-ID (77)"
            ),
        },
        "24": {
            "code": "24",
            "base": 0.0,
            "tax": 0.0,
            "name": _(
                "Umsätze nach § 24 UStG, "
                "z.B. Sägewerke, Getränke u. alk. Flüssigk. (76 / 80)"
            ),
        },
        "25": {
            "code": "25",
            "name": _(
                "Steuerfr. Umsätze mit Vorsteuerabz. innerg. "
                "Lieferungen (§4 Nr. 1b) ..."
            ),
        },
        "26": {
            "code": "26",
            "base": 0.0,
            "name": _("... an Abnehmer mit USt-ID (41)"),
        },
        "27": {
            "code": "27",
            "base": 0.0,
            "name": _("... neuer Fahrzeuge an Abnehmer ohne UST-ID (44)"),
        },
        "28": {
            "code": "28",
            "base": 0.0,
            "name": _(
                "... neuer Fahrzeuge außerh. eines Unternehmens " "§ 2a UStG (49)"
            ),
        },
        "29": {
            "code": "29",
            "base": 0.0,
            "name": _(
                "Weitere steuerfr. Umsätze mit Vorsteuerabzug, "
                "z.B. Ausfuhrlief., Umsätze n. § 4 Nr. 2-7 UStG (43)"
            ),
        },
        "30": {
            "code": "30",
            "base": 0.0,
            "name": _(
                "Steuerfreie Umsätze ohne Vorsteuerabzug "
                "Umsätze n. § 4 Nr. 8 bis 28 UStG (48)"
            ),
        },
        "31": {
            "code": "31",
            "name": _("Innergemeinschaftliche Erwerbe "),
        },
        "32": {
            "code": "32",
            "name": _("Steuerfreie innergemeinschaftliche Erwerbe"),
        },
        "33": {
            "code": "33",
            "base": 0.0,
            "name": _("von best. Gegenst. u. Anlagegold " "§§ 4b u. 25c UStG (91)"),
        },
        "34": {
            "code": "34",
            "base": 0.0,
            "tax": 0.0,
            "name": _(
                "Steuerpflichtige innergemeinschaftliche Erwerbe "
                "... zum Steuersatz v. 19 % (89)"
            ),
        },
        "35": {
            "code": "35",
            "base": 0.0,
            "tax": 0.0,
            "name": _("... zum Steuersatz v. 7% (93)"),
        },
        "36": {
            "code": "36",
            "base": 0.0,
            "tax": 0.0,
            "name": _("... zu anderen Steuersätzen (95 / 98)"),
        },
        "37": {
            "code": "37",
            "base": 0.0,
            "tax": 0.0,
            "name": _(
                "... neuer Fahrzeuge gem. § 1b Abs. 2 u. 3 UStG "
                "von Lieferern o. Ust-ID z. allg. Steuersatz (94 / 96)"
            ),
        },
        "39": {
            "code": "39",
            "name": _("Leistungsempfänger als Steuerschuldner " "(§ 13b UStG)"),
        },
        "40": {
            "code": "40",
            "base": 0.0,
            "tax": 0.0,
            "name": _(
                "Steuerpfl. sonst. Leist. e. i. übr. Gemeinschaftsgeb. "
                "ans. Untern. gem. § 13b Abs. 1 UStG (46 / 47)"
            ),
        },
        "41": {
            "code": "41",
            "base": 0.0,
            "tax": 0.0,
            "name": _(
                "Umsätze, die unter das GrEStG fallen "
                "gem. § 13b Abs. 2 Nr. 3 (73 / 74)"
            ),
        },
        "42": {
            "code": "42",
            "base": 0.0,
            "tax": 0.0,
            "name": _(
                "Andere Leistungen gem. § 13b Abs. 2 Nr. 1, 2," "4 b. 11 UStG (84 / 85)"
            ),
        },
        "47": {"code": "47", "name": _("Ergänzende Angaben zu Umsätzen")},
        "48": {
            "code": "48",
            "base": 0.0,
            "name": _(
                "Lieferungen des ersten Abnehmers bei innergem. "
                "Dreiecksgeschäften gem. § 25b Abs. 2 UStG (42)"
            ),
        },
        "49": {
            "code": "49",
            "base": 0.0,
            "name": _(
                "Übrige steuerpfl. Umsätze f.d.d. Lstg.empf. d. Steuer "
                "n. § 13b Abs. 5 UStG schuldet (60)"
            ),
        },
        "50": {
            "code": "50",
            "base": 0.0,
            "name": _("Nicht steuerb. sonst. Leist. gem. " "§ 18b S. 1 Nr. 2 (21)"),
        },
        "51": {
            "code": "51",
            "base": 0.0,
            "tax": 0.0,
            "name": _(
                "Übrige n. steuerb. Umsätze, Leistungsort " "ist nicht im Inland (45)"
            ),
        },
        "52": {"code": "52", "tax": 0.0, "name": _("Umsatzsteuer")},
        "53": {"code": "53", "name": _("Abziehbare Vorsteuerbeträge")},
        "55": {
            "code": "55",
            "tax": 0.0,
            "name": _(
                "Vorsteuerbeträge aus Rechn. v.a. Unternehmen g. § 15 "
                "Abs. S. 1 Nr. 1 UStG a. Leistungen i.S.d. § 13a "
                "Abs. 1 Nr. 6 UStG u. § 15 Abs. 1 S. 1 Nr. 5 UStG "
                "u. a. innerg. Dreiecksgesch. g. § 25b A. 5 UStG (66)"
            ),
        },
        "56": {
            "code": "56",
            "tax": 0.0,
            "name": _(
                "Vorsteuerbeträge a. d. innerg. Erwerb v. Gegenständen "
                "gem. § 15 Abs. 1 Satz 1 Nr. 3 UStG (61)"
            ),
        },
        "57": {
            "code": "57",
            "tax": 0.0,
            "name": _("Entst. Einfuhrumsatzst. g. § 15 Abs. 1 S. 1 Nr. 2 " "UStG (62)"),
        },
        "58": {
            "code": "58",
            "tax": 0.0,
            "name": _(
                "Vorsteuerbeträge aus Leistungen i. S. des § 13b UStG"
                "i.V.m § 15 Abs. 1 Satz 1 Nr. 4 UStG (67)"
            ),
        },
        "59": {
            "code": "59",
            "tax": 0.0,
            "name": _(
                "Vorsteuerbeträge d. n. allg. Durchschnittssätzen "
                "berechnet sind gem. §§ 23 und 23a UStG (63)"
            ),
        },
        "60": {
            "code": "60",
            "tax": 0.0,
            "name": _(
                "Vorsteuerabzug f. innergem. Lief. neuer Fahrzeuge "
                "außerh. e. Untern. g. §2a UStG sow. v. Kleinunt. i.S. "
                "d. § 19 Abs. 1 i.V.m. § 15a Abs. 4a UStG (59)"
            ),
        },
        "61": {
            "code": "61",
            "tax": 0.0,
            "name": _("Berichtigung des Vorsteuerabzugs g. § 15 a UStG (64)"),
        },
        "62": {"code": "62", "tax": 0.0, "name": _("Verbleibender Betrag")},
        "63": {"code": "63", "name": _("Andere Steuerbeträge")},
        "64": {
            "code": "64",
            "tax": 0.0,
            "name": _(
                "Steuer inf. Wechsels d. Besteuerungsf. sow. Nachst. "
                "a. verst. Anzahlungen u.a. wg. Steuersatzänd. (65)"
            ),
        },
        "65": {
            "code": "65",
            "tax": 0.0,
            "name": _(
                "In Rechnungen unrichtig oder unberechtigt ausgewiesene "
                "Steuerbeträge gem. § 14c UstG) sowie Steuerbetr. d. n. "
                "§ 6a Abs. 4 S. 2, § 17 Abs. 1 S. 6, § 25 b Abs. 2 UStG "
                "o. v. e. Auslagerer o. Lagerh. n. § 13a Abs. 1 Nr. 6 "
                "UStG geschuldet werden (69)"
            ),
        },
        "66": {"code": "66", "tax": 0.0, "name": _("Umsatzsteuer-Vorauszahlung")},
        "67": {
            "code": "67",
            "tax": 0.0,
            "name": _(
                "Abzug der festges. Sondervorauszahl. f. "
                "Dauerfristverlängerung, nur auszuf. i. d. letzten "
                "Voranmeldung d. Besteuerungszeitr., i.d.R. Dez. (39)"
            ),
        },
    }


def _map_tax_code_line_code_2021():
    return {
        "41": "26",
        "44": "27",
        "49": "28",
        "43": "29",
        "48": "30",
        "81": "20",
        "86": "21",
        "35": "22",
        "36": "22",
        "77": "23",
        "76": "24",
        "80": "24",
        "91": "33",
        "89": "34",
        "93": "35",
        "95": "36",
        "98": "36",
        "94": "37",
        "96": "37",
        "42": "48",
        "60": "49",
        "21": "50",
        "45": "51",
        "46": "40",
        "47": "40",
        "73": "41",
        "74": "41",
        "84": "42",
        "85": "42",
        "66": "55",
        "61": "56",
        "62": "57",
        "67": "58",
        "63": "59",
        "64": "61",
        "59": "60",
        "65": "64",
        "69": "65",
        "39": "67",
    }


def _finalize_lines_2021(lines):
    _20b = lines["20"]["tax"]
    _21b = lines["21"]["tax"]
    _22b = lines["22"]["tax"]
    _64b = lines["64"]["tax"]
    _65b = lines["65"]["tax"]
    # calculate reverse of lines 40 - line 42 base
    lines["40"]["base"] = lines["40"]["base"] * -1
    lines["42"]["base"] = lines["42"]["base"] * -1
    # calculate lines 40 - 42
    _40b = lines["40"]["tax"]
    _41b = lines["41"]["tax"]
    lines["42"]["tax"] = lines["42"]["base"] * 0.19
    _42b = lines["42"]["tax"]
    # calculate lines 20, 21, 22, 34, 35
    _22b = lines["22"]["tax"]
    lines["24"]["tax"] = lines["24"]["base"] * 0.19
    _24b = lines["24"]["tax"]

    # calculate reverse of lines 33 - line 37 base
    lines["33"]["base"] = lines["33"]["base"] * -1
    # calculate reverse of lines 33 - line 37 tax
    _34b = lines["34"]["tax"]
    _35b = lines["35"]["tax"]
    lines["36"]["tax"] = lines["36"]["tax"] * -1
    _36b = lines["36"]["tax"]
    _37b = lines["37"]["tax"]
    # calculate reverse of line 55 - line 61
    lines["55"]["tax"] = lines["55"]["tax"] * -1
    _55b = lines["55"]["tax"]
    lines["56"]["tax"] = lines["56"]["tax"] * -1
    _56b = lines["56"]["tax"]
    lines["57"]["tax"] = lines["57"]["tax"] * -1
    _57b = lines["57"]["tax"]
    lines["58"]["tax"] = lines["58"]["tax"] * -1
    _58b = lines["58"]["tax"]
    lines["59"]["tax"] = lines["59"]["tax"] * -1
    _59b = lines["59"]["tax"]
    lines["60"]["tax"] = lines["60"]["tax"] * -1
    _60b = lines["60"]["tax"]
    lines["61"]["tax"] = lines["61"]["tax"] * -1
    _61b = lines["61"]["tax"]
    # calculate line 52
    lines["52"]["tax"] = lines["52"]["tax"] * 1
    _52b = (
        lines["52"]["tax"]
        + _20b
        + _21b
        + _22b
        + _24b
        + _34b
        + _35b
        + _36b
        + _37b
        + _40b
        + _41b
        + _42b
    )

    # calculate line 62
    lines["62"]["tax"] = lines["62"]["tax"] * 1
    _62b = lines["62"]["tax"] + _52b - _55b - _56b - _57b - _58b - _59b - _60b - _61b
    # calculate line 66
    lines["66"]["tax"] = lines["66"]["tax"] * 1
    _66b = lines["66"]["tax"] + _62b + _64b + _65b
    # update lines 52, 62, 66
    lines["66"].update({"tax": _66b})
    lines["52"].update({"tax": _52b})
    lines["62"].update({"tax": _62b})

    # in case it differs from the sign of related tax
    to_be_checked_inverted = ["20", "21", "22", "24", "34", "35", "36", "37"]
    for code in to_be_checked_inverted:
        tax_sign = 1 if lines[code]["tax"] >= 0.0 else -1
        base_sign = 1 if lines[code]["base"] >= 0.0 else -1
        if tax_sign != base_sign:
            lines[code]["base"] *= -1

    return lines


def _totals_2021():
    return ["66", "67"]


def _base_display_2021():
    return (
        "20",
        "21",
        "22",
        "23",
        "24",
        "26",
        "27",
        "28",
        "29",
        "30",
        "33",
        "34",
        "35",
        "36",
        "37",
        "40",
        "41",
        "42",
        "48",
        "49",
        "50",
        "51",
    )


def _tax_display_2021():
    return (
        "20",
        "21",
        "22",
        "24",
        "34",
        "35",
        "36",
        "37",
        "51",
        "40",
        "41",
        "42",
        "52",
        "55",
        "56",
        "57",
        "58",
        "59",
        "60",
        "61",
        "62",
        "64",
        "65",
        "66",
        "67",
    )


def _group_display_2021():
    return (
        "17",
        "18",
        "19",
        "25",
        "31",
        "32",
        "39",
        "47",
        "53",
        "63",
    )


def _editable_display_2021():
    return (
        "20",
        "21",
        "22",
        "23",
        "24",
        "26",
        "27",
        "28",
        "29",
        "30",
        "33",
        "34",
        "35",
        "36",
        "37",
        "40",
        "41",
        "42",
        "48",
        "49",
        "50",
        "51",
        "64",
        "65",
    )


def _total_display_2021():
    return (
        "52",
        "62",
        "66",
        "67",
    )
