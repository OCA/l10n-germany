# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _


def _tax_statement_dict_2019():
    return {
        '17': {
            'code': '17',
            'name': _('Anmeldung der Umsatzsteuer Vorauszahlung'),
        },
        '18': {
            'code': '18',
            'name': _('Lief. u. sonst. Leistg. einschl. unentg. Wertabg.'),
        },
        '19': {
            'code': '19',
            'name': _('Steuerfr. Umsätze mit Vorsteuerabz. innerg. '
                      'Lieferungen (§4 Nr. 1b) ...'),
        },
        '20': {
            'code': '20', 'base': 0.0,
            'name': _('... an Abnehmer mit USt-ID (41)'),
        },
        '21': {
            'code': '21', 'base': 0.0,
            'name': _('... neuer Fahrzeuge an Abnehmer ohne UST-ID (44)'),
        },
        '22': {
            'code': '22', 'base': 0.0,
            'name': _('... neuer Fahrzeuge außerh. eines Unternehmens '
                      '§ 2a UStG (49)'),
        },
        '23': {
            'code': '23', 'base': 0.0,
            'name': _('Weitere steuerfr. Umsätze mit Vorsteuerabzug, '
                      'z.B. Ausfuhrlief., Umsätze n. § 4 Nr. 2-7 UStG (43)'),
        },
        '24': {
            'code': '24', 'base': 0.0,
            'name': _('Steuerfreie Umsätze ohne Vorsteuerabzug '
                      'Umsätze n. § 4 Nr. 8 bis 28 UStG (48)'),
        },
        '25': {
            'code': '25',
            'name': _('Steuerpflichtige Umsätze '
                      '(Lief. u. sonst. Leistg. einschl. unentg. Wertabg.)'),
        },
        '26': {
            'code': '26', 'base': 0.0, 'tax': 0.0,
            'name': _('... zum Steuersatz von 19 % (81)'),
        },
        '27': {
            'code': '27', 'base': 0.0, 'tax': 0.0,
            'name': _('... zum Steuersatz von 7% (86)'),
        },
        '28': {
            'code': '28', 'base': 0.0, 'tax': 0.0,
            'name': _('... zu anderen Steuersätzen (35 / 36)'),
        },
        '29': {
            'code': '29', 'base': 0.0,
            'name': _('Lieferungen land- u. forstw. Betriebe '
                      'nach § 24 UStG an Abnehmer mit Ust-ID (77)'),
        },
        '30': {
            'code': '30', 'base': 0.0, 'tax': 0.0,
            'name': _('Umsätze nach § 24 UStG, '
                      'z.B. Sägewerke, Getränke u. alk. Flüssigk. (76 / 80)'),
        },
        '31': {
            'code': '31',
            'name': _('Innergemeinschaftliche Erwerbe '
                      'Steuerfreie innergemeinschaftliche Erwerbe'),
        },
        '32': {
            'code': '32', 'base': 0.0,
            'name': _('Erwerbe nach §§ 4b u. 25c UStG (91)'),
        },
        '33': {
            'code': '33', 'base': 0.0, 'tax': 0.0,
            'name': _('Steuerpflichtige innergemeinschaftliche Erwerbe '
                      '... zum Steuersatz v. 19 % (89)'),
        },
        '34': {
            'code': '34', 'base': 0.0, 'tax': 0.0,
            'name': _('... zum Steuersatz v. 7% (93)'),
        },
        '35': {
            'code': '35', 'base': 0.0, 'tax': 0.0,
            'name': _('... zu anderen Steuersätzen (95 / 98)'),
        },
        '36': {
            'code': '36', 'base': 0.0, 'tax': 0.0,
            'name': _('... neuer Fahrzeuge gem. § 1b Abs. 2 u. 3 UStG '
                      'von Lieferern o. Ust-ID z. allg. Steuersatz (94 / 96)'),
        },
        '37': {
            'code': '37',
            'name': _('Ergänzende Angaben zu Umsätzen'),
        },
        '38': {
            'code': '38', 'base': 0.0,
            'name': _('Lieferungen des ersten Abnehmers bei innergem. '
                      'Dreiecksgeschäften gem. § 25b Abs. 2 UStG (42)'),
        },
        '39': {
            'code': '39', 'base': 0.0,
            'name': _('Übrige steuerpfl. Umsätze f.d.d. Lstg.empf. d. Steuer '
                      'n. § 13b Abs. 5 UStG schuldet (60)'),
        },
        '40': {
            'code': '40', 'base': 0.0,
            'name': _('Nicht steuerb. sonst. Leist. gem. '
                      '§ 18b S. 1 Nr. 2 (21)'),
        },
        '41': {
            'code': '41', 'base': 0.0,
            'name': _('Übrige n. steuerb. Umsätze, Leistungsort '
                      'ist nicht im Inland (45)'),
        },
        '47': {
            'code': '47',
            'name': _('Leistungsempfänger als Steuerschuldner '
                      '(§ 13b UStG)'),
        },
        '48': {
            'code': '48', 'base': 0.0, 'tax': 0.0,
            'name': _('Steuerpfl. sonst. Leist. e. i. übr. Gemeinschaftsgeb. '
                      'ans. Untern. gem. § 13b Abs. 1 UStG (46 / 47)'),
        },
        '49': {
            'code': '49', 'base': 0.0, 'tax': 0.0,
            'name': _('Lieferungen sicherungsübereign. Gegenst. u. Umsätze '
                      'd. u. d.  GrEStG fallen g. § 13b Abs. 2 '
                      'Nr. 3 (73 / 74)'),
        },
        '50': {
            'code': '50', 'base': 0.0, 'tax': 0.0,
            'name': _('Andere Leistungen gem. § 13b Abs. 2 Nr. 1, 2,'
                      '4 b. 11 UStG (84 / 85)'),
        },
        '51': {
            'code': '51', 'tax': 0.0,
            'name': _('Umsatzsteuer'),
        },
        '52': {
            'code': '52',
            'name': _('Abziehbare Vorsteuerbeträge'),
        },
        '53': {
            'code': '53', 'tax': 0.0,
            'name': _('Vorsteuerbeträge aus Rechn. v.a. Unternehmen g. § 15 '
                      'Abs. S. 1 Nr. 1 UStG a. Leistungen i.S.d. § 13a '
                      'Abs. 1 Nr. 6 UStG u. § 15 Abs. 1 S. 1 Nr. 5 UStG '
                      'u. a. innerg. Dreiecksgesch. g. § 25b A. 5 UStG (66)'),
        },
        '54': {
            'code': '54', 'tax': 0.0,
            'name': _('Vorsteuerbeträge a. d. innerg. Erwerb v. Gegenständen '
                      'gem. § 15 Abs. 1 Satz 1 Nr. 3 UStG (61)'),
        },
        '55': {
            'code': '55', 'tax': 0.0,
            'name': _('Entst. Einfuhrumsatzst. g. § 15 Abs. 1 S. 1 Nr. 2 '
                      'UStG (62)'),
        },
        '56': {
            'code': '56', 'tax': 0.0,
            'name': _('Vorsteuerbeträge aus Leistungen i. S. des § 13b UStG'
                      'i.V.m § 15 Abs. 1 Satz 1 Nr. 4 UStG (67)'),
        },
        '57': {
            'code': '57', 'tax': 0.0,
            'name': _('Vorsteuerbeträge d. n. allg. Durchschnittssätzen '
                      'berechnet sind gem. §§ 23 und 23a UStG (63)'),
        },
        '58': {
            'code': '58', 'tax': 0.0,
            'name': _('Berichtigung des Vorsteuerabzugs g. § 15 a UStG (64)'),
        },
        '59': {
            'code': '59', 'tax': 0.0,
            'name': _('Vorsteuerabzug f. innergem. Lief. neuer Fahrzeuge '
                      'außerh. e. Untern. g. §2a UStG sow. v. Kleinunt. i.S. '
                      'd. § 19 Abs. 1 i.V.m. § 15a Abs. 4a UStG (59)'),
        },
        '60': {
            'code': '60', 'tax': 0.0,
            'name': _('Verbleibender Betrag'),
        },
        '61': {
            'code': '61',
            'name': _('Andere Steuerbeträge'),
        },
        '62': {
            'code': '62', 'tax': 0.0,
            'name': _('Steuer inf. Wechsels d. Besteuerungsf. sow. Nachst. '
                      'a. verst. Anzahlungen u.a. wg. Steuersatzänd. (65)'),
        },
        '63': {
            'code': '63', 'tax': 0.0,
            'name': _('In Rechnungen unrichtig oder unberechtigt ausgewiesene '
                      'Steuerbeträge gem. § 14c UstG) sowie Steuerbetr. d. n. '
                      '§ 6a Abs. 4 S. 2, § 17 Abs. 1 S. 6, § 25 b Abs. 2 UStG '
                      'o. v. e. Auslagerer o. Lagerh. n. § 13a Abs. 1 Nr. 6 '
                      'UStG geschuldet werden (69)'),
        },
        '64': {
            'code': '64', 'tax': 0.0,
            'name': _('Umsatzsteuer-Vorauszahlung'),
        },
        '65': {
            'code': '65', 'tax': 0.0,
            'name': _('Abzug der festges. Sondervorauszahl. f. '
                      'Dauerfristverlängerung, nur auszuf. i. d. letzten '
                      'Voranmeldung d. Besteuerungszeitr., i.d.R. Dez. (39)'),
        },
    }


def _finalize_lines_2019(lines):
    _26b = lines['26']['tax']
    _27b = lines['27']['tax']
    _28b = lines['28']['tax']
    _62b = lines['62']['tax']
    _63b = lines['63']['tax']
    # calculate lines 48 - 50
    lines['48']['tax'] = lines['48']['tax'] * 1
    _48b = lines['48']['tax']
    lines['49']['tax'] = lines['49']['tax'] * 1
    _49b = lines['49']['tax']
    lines['50']['tax'] = lines['50']['tax'] * 1
    _50b = lines['50']['tax']
    # calculate lines 26, 27, 28, 33, 34
    lines['26']['tax'] = lines['26']['base'] * 0.19
    _26b = lines['26']['tax']
    lines['27']['tax'] = lines['27']['base'] * 0.07
    _27b = lines['27']['tax']
    lines['30']['tax'] = lines['30']['base'] * 0.19
    _30b = lines['30']['tax']
    lines['33']['tax'] = lines['33']['base'] * 0.19
    _33b = lines['33']['tax']
    lines['34']['tax'] = lines['34']['base'] * 0.07
    _34b = lines['34']['tax']
    # calculate reverse of lines 32 - line 36 base
    lines['32']['base'] = lines['32']['base'] * -1
    lines['33']['base'] = lines['33']['base'] * -1
    lines['34']['base'] = lines['34']['base'] * -1
    lines['35']['base'] = lines['35']['base'] * -1
    lines['36']['base'] = lines['36']['base'] * -1
    # calculate reverse of lines 32 - line 36 tax
    lines['33']['tax'] = lines['33']['tax'] * -1
    _33b = lines['33']['tax']
    lines['34']['tax'] = lines['34']['tax'] * -1
    _34b = lines['34']['tax']
    lines['35']['tax'] = lines['35']['tax'] * -1
    _35b = lines['35']['tax']
    lines['36']['tax'] = lines['36']['tax'] * -1
    _36b = lines['36']['tax']
    # calculate reverse of lines 48 - line 50 base
    lines['48']['base'] = lines['48']['base'] * -1
    lines['49']['base'] = lines['49']['base'] * -1
    lines['50']['base'] = lines['50']['base'] * -1
    # calculate reverse of line 53 - line 59
    lines['53']['tax'] = lines['53']['tax'] * -1
    _53b = lines['53']['tax']
    lines['54']['tax'] = lines['54']['tax'] * -1
    _54b = lines['54']['tax']
    lines['55']['tax'] = lines['55']['tax'] * -1
    _55b = lines['55']['tax']
    lines['56']['tax'] = lines['56']['tax'] * -1
    _56b = lines['56']['tax']
    lines['57']['tax'] = lines['57']['tax'] * -1
    _57b = lines['57']['tax']
    lines['58']['tax'] = lines['58']['tax'] * -1
    _58b = lines['58']['tax']
    lines['59']['tax'] = lines['59']['tax'] * -1
    _59b = lines['59']['tax']
    # calculate line 51
    lines['51']['tax'] = lines['51']['tax'] * 1
    _51b = lines['51']['tax'] + _26b + _27b + _28b + _30b + _33b + _34b \
        + _35b + _36b + _48b + _49b + _50b
    # calculate line 60
    lines['60']['tax'] = lines['60']['tax'] * 1
    _60b = lines['60']['tax'] + _51b - _53b - _54b - _55b \
        - _56b - _57b - _58b - _59b
    # calculate line 64
    lines['64']['tax'] = lines['64']['tax'] * 1
    _64b = lines['64']['tax'] + _60b + _62b + _63b
    # update lines 51, 60, 64
    lines['64'].update({'tax': _64b})
    lines['51'].update({'tax': _51b})
    lines['60'].update({'tax': _60b})


def _get_tags_map_2019(config):
    return {
        config.tag_41_base.id: ('20', 'base'),
        config.tag_44_base.id: ('21', 'base'),
        config.tag_49_base.id: ('22', 'base'),
        config.tag_43_base.id: ('23', 'base'),
        config.tag_48_base.id: ('24', 'base'),
        config.tag_81_base.id: ('26', 'base'),
        config.tag_81_tax.id: ('26', 'tax'),
        config.tag_86_base.id: ('27', 'base'),
        config.tag_86_tax.id: ('27', 'tax'),
        config.tag_35_base.id: ('28', 'base'),
        config.tag_36_tax.id: ('28', 'tax'),
        config.tag_77_base.id: ('29', 'base'),
        config.tag_76_base.id: ('30', 'base'),
        config.tag_80_tax.id: ('30', 'tax'),
        config.tag_91_base.id: ('32', 'base'),
        config.tag_89_base.id: ('33', 'base'),
        config.tag_93_base.id: ('34', 'base'),
        config.tag_95_base.id: ('35', 'base'),
        config.tag_98_tax.id: ('35', 'tax'),
        config.tag_94_base.id: ('36', 'base'),
        config.tag_96_tax.id: ('36', 'tax'),
        config.tag_42_base.id: ('38', 'base'),
        config.tag_68_base.id: ('39', 'base'),
        config.tag_60_base.id: ('39', 'base'),
        config.tag_21_base.id: ('40', 'base'),
        config.tag_45_base.id: ('41', 'base'),
        config.tag_46_base.id: ('48', 'base'),
        config.tag_47_tax.id: ('48', 'tax'),
        config.tag_73_base.id: ('49', 'base'),
        config.tag_74_tax.id: ('49', 'tax'),
        config.tag_52_base.id: ('50', 'base'),
        config.tag_53_tax.id: ('50', 'tax'),
        config.tag_78_base.id: ('50', 'base'),
        config.tag_79_tax.id: ('50', 'tax'),
        config.tag_84_base.id: ('50', 'base'),
        config.tag_85_tax.id: ('50', 'tax'),
        config.tag_66_tax.id: ('53', 'tax'),
        config.tag_61_tax.id: ('54', 'tax'),
        config.tag_62_tax.id: ('55', 'tax'),
        config.tag_67_tax.id: ('56', 'tax'),
        config.tag_63_tax.id: ('57', 'tax'),
        config.tag_64_tax.id: ('58', 'tax'),
        config.tag_59_tax.id: ('59', 'tax'),
        config.tag_65_tax.id: ('62', 'tax'),
        config.tag_69_tax.id: ('63', 'tax'),
    }


def _totals_2019():
    return ['64', '65']


def _base_display_2019():
    return (
        '20', '21', '22', '23', '24',
        '26', '27', '28', '29', '30',
        '32', '33', '34', '35', '36',
        '38', '39', '40', '41', '48',
        '49', '50',
    )


def _tax_display_2019():
    return (
        '26', '27', '28', '30',
        '33', '34', '35', '36',
        '48', '49', '50', '51',
        '53', '54', '55', '56',
        '57', '58', '59', '60',
        '62', '63', '64', '65',
    )


def _group_display_2019():
    return (
        '17', '18', '19',
        '25', '31', '37',
        '47', '52', '61',
    )


def _editable_display_2019():
    return (
        '20', '21', '22', '23', '24',
        '26', '27', '28', '29', '30',
        '32', '33', '34', '35', '36',
        '38', '39', '40', '41', '42',
        '48', '49', '50', '64', '65',
    )


def _total_display_2019():
    return (
        '51', '60',
    )
