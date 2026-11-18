# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The ELSTER configuration of the statement: the rows of the form with
their Kennzahlen and tax tags, their positions in the ELSTER schema and the
constants of the ELSTER XML."""

USTVA_NAMESPACE = "http://finkonsens.de/elster/elsteranmeldung/ustva/v{year}"
HERSTELLER_ID_PARAM = "l10n_de_tax_statement.elster_hersteller_id"


# How the tax amount of a row adds up to Kennzahl 83
DUE = 1
DEDUCTIBLE = -1
INFO = 0


def _section(name):
    return {"display_type": "line_section", "name": name}


def _row(
    name,
    base_code=False,
    tax_code=False,
    base_tag=None,
    tax_tag=None,
    kind=DUE,
    xml=None,
    not_negative=False,
):
    """A row of the ELSTER form. The tags default to the Kennzahl, the tax of
    some rows has no Kennzahl of its own as ELSTER computes it from the base.
    xml is the position of the Kennzahl in the ELSTER schema, a pair of
    positions for a row with a base and a tax Kennzahl."""
    codes = [code for code in (base_code, tax_code) if code]
    positions = xml if isinstance(xml, tuple) else (xml,)
    return {
        "name": name,
        "base_code": base_code,
        "base_tag": base_tag or base_code or False,
        "tax_code": tax_code,
        "tax_tag": tax_tag or tax_code or False,
        "kind": kind,
        "xml": dict(zip(codes, positions, strict=True)),
        "not_negative": not_negative,
    }


# The rows of the ELSTER form, in the order of the form, the one place which
# knows the Kennzahlen. Update creates one statement line from each of them,
# the XML export takes the order and the checks of the Kennzahlen from them.
#
# A row puts the base and the tax which belong together side by side, like the
# form does, e.g. Kz35 and Kz36. Some taxes have no Kennzahl of their own,
# ELSTER computes them from the base, e.g. the tax of Kz81.
# The amounts come from the tax tags of l10n_de, which are named after the
# Kennzahlen ("81_BASE", "81_TAX", "66", ...). The taxes carry these tags, so a
# tax only needs the right tags to end up in the right row.
# The kind tells how the tax of a row adds up to Kennzahl 83: tax due adds,
# deductible input tax and Kz39 subtract, Kz37 and Kz50 are just information.
# not_negative marks the Kennzahlen the schema doesn't allow to be negative.
#
# xml is the position of the Kennzahl in the ELSTER schema. The schema defines
# the Kennzahlen as an xs:sequence, so the XML has to follow its order, which
# isn't the order of the form. It is almost numerical, but Kennzahlen added
# later sit where the schema put them, e.g. 90 (since 2023) follows 93. The
# positions follow the complex type Umsatzsteuervoranmeldung of UStVA-<year>.xsd
# of the ERiC documentation, which has the same order in every year since 2021.
# Kennzahl 83 has no row, it is computed from the rows, see
# TOTAL_XML_POSITION. Kennzahlen of the schema the statement doesn't support
# are left out, see the roadmap of the module.
#
# The rows are the same for every year, a year only adds or removes some
# Kennzahlen, e.g. 87 and 90 exist since 2023. The export doesn't check them by
# year, ERiC validates the XML against the schema of its year anyway. The
# labels are kept in German like on the form.
STATEMENT_ROWS = [
    _section("Lieferungen und sonstige Leistungen"),
    _row("zum Steuersatz von 19 %", "81", base_tag="81_BASE", tax_tag="81_TAX", xml=31),
    _row("zum Steuersatz von 7 %", "86", base_tag="86_BASE", tax_tag="86_TAX", xml=35),
    _row("zum Steuersatz von 0 % (§ 12 Abs. 3 UStG)", "87", xml=36),
    _row("zu anderen Steuersätzen", "35", "36", xml=(2, 3)),
    _row(
        "Lieferungen land- und forstwirtschaftlicher Betriebe nach § 24 UStG "
        "an Abnehmer mit USt-IdNr.",
        "77",
        xml=29,
    ),
    _row(
        "Umsätze, für die eine Steuer nach § 24 UStG zu entrichten ist",
        "76",
        "80",
        xml=(28, 30),
    ),
    _section("Steuerfreie Umsätze mit Vorsteuerabzug"),
    _row("Innergemeinschaftliche Lieferungen an Abnehmer mit USt-IdNr.", "41", xml=6),
    _row(
        "Innergemeinschaftliche Lieferungen neuer Fahrzeuge an Abnehmer ohne "
        "USt-IdNr.",
        "44",
        xml=9,
    ),
    _row(
        "Innergemeinschaftliche Lieferungen neuer Fahrzeuge außerhalb eines "
        "Unternehmens (§ 2a UStG)",
        "49",
        xml=14,
    ),
    _row("Weitere steuerfreie Umsätze mit Vorsteuerabzug", "43", xml=8),
    _section("Steuerfreie Umsätze ohne Vorsteuerabzug"),
    _row("Umsätze nach § 4 Nr. 8 bis 29 oder § 19 Abs. 1 UStG", "48", xml=13),
    _section("Innergemeinschaftliche Erwerbe"),
    _row("Steuerfreie innergemeinschaftliche Erwerbe", "91", xml=38),
    _row("zum Steuersatz von 19 %", "89", base_tag="89_BASE", tax_tag="89_TAX", xml=37),
    _row("zum Steuersatz von 7 %", "93", base_tag="93_BASE", tax_tag="93_TAX", xml=39),
    _row("zum Steuersatz von 0 %", "90", xml=40),
    _row("zu anderen Steuersätzen", "95", "98", xml=(42, 44)),
    _row(
        "Neue Fahrzeuge von Lieferern ohne USt-IdNr. zum allgemeinen Steuersatz",
        "94",
        "96",
        xml=(41, 43),
    ),
    _section("Leistungsempfänger als Steuerschuldner (§ 13b UStG)"),
    _row(
        "Sonstige Leistungen eines im übrigen Gemeinschaftsgebiet ansässigen "
        "Unternehmers (§ 13b Abs. 1 UStG)",
        "46",
        "47",
        xml=(11, 12),
    ),
    _row(
        "Lieferungen sicherungsübereigneter Gegenstände und Umsätze, die unter "
        "das GrEStG fallen (§ 13b Abs. 2 Nr. 2 und 3 UStG)",
        "73",
        "74",
        xml=(26, 27),
    ),
    _row(
        "Andere Leistungen (§ 13b Abs. 2 Nr. 1, 4 bis 12 UStG)",
        "84",
        "85",
        xml=(33, 34),
    ),
    _section("Ergänzende Angaben zu Umsätzen"),
    _row(
        "Lieferungen des ersten Abnehmers bei innergemeinschaftlichen "
        "Dreiecksgeschäften (§ 25b Abs. 2 UStG)",
        "42",
        xml=7,
    ),
    _row(
        "Steuerpflichtige Umsätze, für die der Leistungsempfänger die Steuer "
        "nach § 13b Abs. 5 UStG schuldet",
        "60",
        xml=17,
    ),
    _row("Nicht steuerbare sonstige Leistungen (§ 18b Satz 1 Nr. 2 UStG)", "21", xml=1),
    _row(
        "Übrige nicht steuerbare Umsätze (Leistungsort nicht im Inland)",
        "45",
        base_tag="45_BASE",
        xml=10,
    ),
    _section("Abziehbare Vorsteuerbeträge"),
    _row(
        "Vorsteuerbeträge aus Rechnungen von anderen Unternehmern",
        tax_code="66",
        kind=DEDUCTIBLE,
        xml=23,
    ),
    _row(
        "Vorsteuerbeträge aus dem innergemeinschaftlichen Erwerb von Gegenständen",
        tax_code="61",
        kind=DEDUCTIBLE,
        xml=18,
    ),
    _row("Entstandene Einfuhrumsatzsteuer", tax_code="62", kind=DEDUCTIBLE, xml=19),
    _row(
        "Vorsteuerbeträge aus Leistungen im Sinne des § 13b UStG",
        tax_code="67",
        kind=DEDUCTIBLE,
        xml=24,
    ),
    _row(
        "Vorsteuerbeträge, die nach allgemeinen Durchschnittssätzen berechnet "
        "sind (§§ 23, 23a UStG)",
        tax_code="63",
        kind=DEDUCTIBLE,
        xml=20,
    ),
    _row(
        "Vorsteuerabzug für innergemeinschaftliche Lieferungen neuer Fahrzeuge "
        "außerhalb eines Unternehmens (§ 2a UStG)",
        tax_code="59",
        kind=DEDUCTIBLE,
        xml=16,
    ),
    _row(
        "Berichtigung des Vorsteuerabzugs (§ 15a UStG)",
        tax_code="64",
        kind=DEDUCTIBLE,
        xml=21,
    ),
    _section("Andere Steuerbeträge"),
    _row(
        "Steuer infolge Wechsels der Besteuerungsform sowie Nachsteuer auf "
        "versteuerte Anzahlungen u. ä. wegen Steuersatzänderung",
        tax_code="65",
        xml=22,
    ),
    _row(
        "In Rechnungen unrichtig oder unberechtigt ausgewiesene Steuerbeträge "
        "(§ 14c UStG)",
        tax_code="69",
        xml=25,
    ),
    _row(
        "Abzug der festgesetzten Sondervorauszahlung für Dauerfristverlängerung",
        tax_code="39",
        kind=DEDUCTIBLE,
        xml=5,
        not_negative=True,
    ),
    _section("Minderungen nach § 17 UStG (in den Beträgen oben enthalten)"),
    _row(
        "Minderung der Bemessungsgrundlage", "50", kind=INFO, xml=15, not_negative=True
    ),
    _row(
        "Minderung der abziehbaren Vorsteuerbeträge",
        tax_code="37",
        kind=INFO,
        xml=4,
        not_negative=True,
    ),
]
# The tax tags the rows sum up, see STATEMENT_ROWS. The amounts of other tax
# tags, e.g. a renamed or a custom one, have no Kennzahl and aren't declared,
# the statement shows them in a section of their own.
ROW_TAGS = {
    tag
    for row in STATEMENT_ROWS
    for tag in (row.get("base_tag"), row.get("tax_tag"))
    if tag
}
OTHER_TAGS_SECTION = "Steuer-Tags ohne Kennzahl (nicht gemeldet)"
# The position of Kennzahl 83 in the ELSTER schema, see STATEMENT_ROWS
TOTAL_XML_POSITION = 32
# The Kennzahlen by their position in the ELSTER schema and the ones which
# can't be negative, both taken from STATEMENT_ROWS
XML_POSITIONS = {
    code: position
    for row in STATEMENT_ROWS
    for code, position in row.get("xml", {}).items()
} | {"83": TOTAL_XML_POSITION}
NOT_NEGATIVE = {
    code for row in STATEMENT_ROWS if row.get("not_negative") for code in row["xml"]
}
