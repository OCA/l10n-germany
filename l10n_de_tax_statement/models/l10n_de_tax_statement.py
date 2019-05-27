# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang


class VatStatement(models.Model):
    _name = 'l10n.de.tax.statement'
    _description = 'German Vat Statement'

    name = fields.Char(
        string='Tax Statement',
        required=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('final', 'Final')],
        readonly=True,
        default='draft',
        copy=False,
        string='Status'
    )
    line_ids = fields.One2many(
        'l10n.de.tax.statement.line',
        'statement_id',
        'Lines'
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id
    )
    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    date_range_id = fields.Many2one(
        'date.range',
        'Date range',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True
    )
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')],
        'Target Moves',
        readonly=True,
        required=True,
        default='posted'
    )
    date_posted = fields.Datetime(readonly=True)
    date_update = fields.Datetime(readonly=True)

    tax_total = fields.Monetary(
        compute='_compute_tax_total',
        string='Verbl. Ust.-Vorauszahlung (66 - 67)'
    )
    format_tax_total = fields.Char(
        compute='_compute_amount_format_tax_total',
        string='Verbl. Ust.-Vorauszahlung'
    )
    move_line_ids = fields.One2many(
        'account.move.line',
        'l10n_de_tax_statement_id',
        string='Entry Lines',
        readonly=True,
    )

    @api.multi
    def _compute_unreported_move_ids(self):
        for statement in self:
            domain = statement._get_unreported_move_domain()
            move_lines = self.env['account.move.line'].search(domain)
            moves = move_lines.mapped('move_id').sorted('date')
            statement.unreported_move_ids = moves

    @api.multi
    def _get_unreported_move_domain(self):
        self.ensure_one()
        domain = [
            ('company_id', '=', self.company_id.id),
            ('invoice_id', '!=', False),
            ('l10n_de_tax_statement_id', '=', False),
            ('date', '<', self.from_date),
        ]
        if self.unreported_move_from_date:
            domain += [
                ('date', '>=', self.unreported_move_from_date),
            ]
        return domain

    unreported_move_ids = fields.One2many(
        'account.move',
        string="Unreported Journal Entries",
        compute='_compute_unreported_move_ids'
    )
    unreported_move_from_date = fields.Date()

    @api.multi
    @api.depends('tax_total')
    def _compute_amount_format_tax_total(self):
        for statement in self:
            tax = formatLang(self.env, statement.tax_total, monetary=True)
            statement.format_tax_total = tax

    @api.model
    def default_get(self, fields_list):
        defaults = super(VatStatement, self).default_get(fields_list)
        company = self.env.user.company_id
        fy_dates = company.compute_fiscalyear_dates(datetime.now())
        from_date = fields.Date.to_string(fy_dates['date_from'])
        to_date = fields.Date.to_string(fy_dates['date_to'])
        defaults.setdefault('from_date', from_date)
        defaults.setdefault('to_date', to_date)
        defaults.setdefault('name', company.name)
        return defaults

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id and self.state == 'draft':
            self.update({
                'from_date': self.date_range_id.date_start,
                'to_date': self.date_range_id.date_end,
            })

    @api.onchange('from_date', 'to_date')
    def onchange_date(self):
        display_name = self.company_id.name
        if self.from_date and self.to_date:
            display_name += ': ' + ' '.join([self.from_date, self.to_date])
        self.name = display_name

    @api.onchange('from_date')
    def onchange_date_from_date(self):
        d_from = datetime.strptime(self.from_date, DF)
        # by default the unreported_move_from_date is set to
        # a quarter (three months) before the from_date of the statement
        d_from_2months = d_from + relativedelta(months=-3, day=1)
        date_from = fields.Date.to_string(d_from_2months)
        self.unreported_move_from_date = date_from

    @api.onchange('unreported_move_from_date')
    def onchange_unreported_move_from_date(self):
        self._compute_unreported_move_ids()

    @api.model
    def _get_taxes_domain(self):
        return [('has_moves', '=', True)]

    @api.model
    def _prepare_lines(self):
        lines = {}
        lines['17'] = {
            'code': '17',
            'name': _('Anmeldung der Umsatzsteuer Vorauszahlung')}
        lines['18'] = {
            'code': '18',
            'name': _('Lief. u. sonst. Leistg. einschl. unentg. Wertabg.')}
        lines['19'] = {
            'code': '19',
            'name': _('Steuerfr. Umsätze mit Vorsteuerabz. innerg. '
                      'Lieferungen (§4 Nr. 1b) ...')}
        lines['20'] = {
            'code': '20', 'base': 0.0,
            'name': _('... an Abnehmer mit USt-ID (41)')}
        lines['21'] = {
            'code': '21', 'base': 0.0,
            'name': _('... neue Fahrzeuge an Abnehmer ohne UST-ID (44)')}
        lines['22'] = {
            'code': '22', 'base': 0.0,
            'name': _('... neuer Fahrzeuge außerh. eines Unternehmens '
                      '§ 2a UStG (49)')}
        lines['23'] = {
            'code': '23', 'base': 0.0,
            'name': _('Weitere steuerfr. Umsätze mit Vorsteuerabzug, '
                      'z.B. Ausfuhrlief., Umsätze n. § 4 Nr. 2-7 UStG (43)')}
        lines['24'] = {
            'code': '24', 'base': 0.0,
            'name': _('Steuerfreie Umsätze ohne Vorsteuerabzug '
                      'Umsätze n. § 4 Nr. 8 bis 28 UStG (48)')}
        lines['25'] = {
            'code': '25',
            'name': _('Steuerpflichtige Umsätze '
                      '(Lief. u. sonst. Leistg. einschl. unentg. Wertabg.)')}
        lines['26'] = {
            'code': '26', 'base': 0.0, 'tax': 0.0,
            'name': _('... zum Steuersatz von 19 % (81)')}
        lines['27'] = {
            'code': '27', 'base': 0.0, 'tax': 0.0,
            'name': _('... zum Steuersatz von 7% (86)')}
        lines['28'] = {
            'code': '28', 'base': 0.0, 'tax': 0.0,
            'name': _('... zu anderen Steuersätzen (35 / 36)')}
        lines['29'] = {
            'code': '29', 'base': 0.0,
            'name': _('Lieferungen land- u. forstw. Betriebe '
                      'nach § 24 UStG an Abnehmer mit Ust-ID (77)')}
        lines['30'] = {
            'code': '30', 'base': 0.0, 'tax': 0.0,
            'name': _('Umsätze nach § 24 UStG, '
                      'z.B. Sägewerke, Getränke u. alk. Flüssigk. (76 / 80)')}
        lines['31'] = {
            'code': '31',
            'name': _('Innergemeinschaftliche Erwerbe '
                      'Steuerfreie innergemeinschaftliche Erwerbe')}
        lines['32'] = {
            'code': '32', 'base': 0.0,
            'name': _('Erwerbe nach §§ 4b u. 25c UStG (91)')}
        lines['33'] = {
            'code': '33', 'base': 0.0, 'tax': 0.0,
            'name': _('Steuerpflichtige innergemeinschaftliche Erwerbe '
                      '... zum Steuersatz v. 19 % (89)')}
        lines['34'] = {
            'code': '34', 'base': 0.0, 'tax': 0.0,
            'name': _('... zum Steuersatz v. 7% (93)')}
        lines['35'] = {
            'code': '35', 'base': 0.0, 'tax': 0.0,
            'name': _('... zu anderen Steuersätzen (95 / 98)')}
        lines['36'] = {
            'code': '36', 'base': 0.0, 'tax': 0.0,
            'name': _('... neuer Fahrzeuge gem. § 1b Abs. 2 u. 3 UStG '
                      'von Lieferern o. Ust-ID z. allg. Steuersatz (94 / 96)')}
        lines['37'] = {
            'code': '37', 'base': 0.0, 'tax': 0.0,
            'name': _('Ergänzende Angaben zu Umsätzen')}
        lines['38'] = {
            'code': '38', 'base': 0.0,
            'name': _('Lieferungen des ersten Abnehmers bei innergem. '
                      'Dreiecksgeschäften gem. § 25b Abs. 2 UStG (42)')}
        lines['39'] = {
            'code': '39', 'base': 0.0,
            'name': _('Steuerpfl. Ums. f.d.d. Leistungsempf. die Steuer '
                      'schuldet g. § 13b A. 5 S. 1 i.V.m. Abs. 2 '
                      'Nr. 10 UStG (68)')}
        lines['40'] = {
            'code': '40', 'base': 0.0,
            'name': _('Übrige steuerpfl. Umsätze f.d.d. Lstg.empf. d. Steuer '
                      'n. § 13b Abs. 5 UStG schuldet (60)')}
        lines['41'] = {
            'code': '41', 'base': 0.0,
            'name': _('Nicht steuerb. sonst. Leist. gem. '
                      '§ 18b S. 1 Nr. 2 (21)')}
        lines['42'] = {
            'code': '42', 'base': 0.0,
            'name': _('Übrige n. steuerb. Umsätze, Leistungsort '
                      'ist nicht im Inland (45)')}
        lines['47'] = {
            'code': '47',
            'name': _('Leistungsempfänger als Steuerschuldner '
                      '(§ 13b UStG)')}
        lines['48'] = {
            'code': '48', 'base': 0.0, 'tax': 0.0,
            'name': _('Steuerpfl. sonst. Leist. e. i. übr. Gemeinschaftsgeb. '
                      'ans. Untern. gem. § 13b Abs. 1 UStG (46 / 47)')}
        lines['49'] = {
            'code': '49', 'base': 0.0, 'tax': 0.0,
            'name': _('Andere Leistung eines im Ausland ansässigen Untern. '
                      'gem. § 13b Abs. 2 Nr. 1 u. 5 Buchst. a UStG (52 / 53)')}
        lines['50'] = {
            'code': '50', 'base': 0.0, 'tax': 0.0,
            'name': _('Lieferungen sicherungsübereign. Gegenst. u. Umsätze '
                      'd. u. d.  GrEStG fallen g. § 13b Abs. 2 '
                      'Nr. 2 u. 3 (73 / 74)')}
        lines['51'] = {
            'code': '51', 'base': 0.0, 'tax': 0.0,
            'name': _('Lieferungen v. Mobilfunkger., Tablet-Comp., '
                      'Spielekons. u. int. Schaltkr. g. §13b A. 2 '
                      'Nr. 10 UStG (78 / 79)')}
        lines['52'] = {
            'code': '52', 'base': 0.0, 'tax': 0.0,
            'name': _('Andere Leistungen gem. § 13b Abs. 2 Nr. 4, 5 '
                      'Bst. b, Nr. 6 b. 9 u. 11 UStG (84 / 85)')}
#        lines['53'] = {
#            'code': '53', 'tax': 0.0,
#            'name': _('Steuer inf. Wechsels d. Besteuerungsf. sow. Nachst. '
#                      'a. verst. Anzahlungen u.a. wg. Steuersatzänd. (65)')}
        lines['53'] = {
            'code': '53', 'tax': 0.0,
            'name': _('Umsatzsteuer')}
        lines['54'] = {
            'code': '54',
            'name': _('Abziehbare Vorsteuerbeträge')}
        lines['55'] = {
            'code': '55', 'tax': 0.0,
            'name': _('Vorsteuerbeträge aus Rechn. v.a. Unternehmen g. § 15 '
                      'Abs. S. 1 Nr. 1 UStG a. Leistungen i.S.d. § 13a '
                      'Abs. 1 Nr. 6 UStG u. § 15 Abs. 1 S. 1 Nr. 5 UStG '
                      'u. a. innerg. Dreiecksgesch. g. § 25b A. 5 UStG (66)')}
        lines['56'] = {
            'code': '56', 'tax': 0.0,
            'name': _('Vorsteuerbeträge a. d. innerg. Erwerb v. Gegenständen '
                      'gem. § 15 Abs. 1 Satz 1 Nr. 3 UStG (61)')}
        lines['57'] = {
            'code': '57', 'tax': 0.0,
            'name': _('Entst. Einfuhrumsatzst. g. § 15 Abs. 1 S. 1 Nr. 2 '
                      'UStG (62)')}
        lines['58'] = {
            'code': '58', 'tax': 0.0,
            'name': _('Vorsteuerbeträge aus Leistungen i. S. des § 13b UStG'
                      'i.V.m § 15 Abs. 1 Satz 1 Nr. 4 UStG (67)')}
        lines['59'] = {
            'code': '59', 'tax': 0.0,
            'name': _('Vorsteuerbeträge d. n. allg. Durchschnittssätzen '
                      'berechnet sind gem. §§ 23 und 23a UStG (63)')}
        lines['60'] = {
            'code': '60', 'tax': 0.0,
            'name': _('Berichtigung des Vorsteuerabzugs g. § 15 a UStG (64)')}
        lines['61'] = {
            'code': '61', 'tax': 0.0,
            'name': _('Vorsteuerabzug f. innergem. Lief. neuer Fahrzeuge '
                      'außerh. e. Untern. g. §2a UStG sow. v. Kleinunt. i.S. '
                      'd. § 19 Abs. 1 i.V.m. § 15a Abs. 4a UStG (59)')}
        lines['62'] = {
            'code': '62', 'tax': 0.0,
            'name': _('Verbleibender Betrag')}
        lines['63'] = {
            'code': '63',
            'name': _('Andere Steuerbeträge')}
        lines['64'] = {
            'code': '64', 'tax': 0.0,
            'name': _('Steuer inf. Wechsels d. Besteuerungsf. sow. Nachst. '
                      'a. verst. Anzahlungen u.a. wg. Steuersatzänd. (65)')}
        lines['65'] = {
            'code': '65', 'tax': 0.0,
            'name': _('In Rechnungen unrichtig oder unberechtigt ausgewiesene '
                      'Steuerbeträge gem. § 14c UstG) sowie Steuerbetr. d. n. '
                      '§ 6a Abs. 4 S. 2, § 17 Abs. 1 S. 6, § 25 b Abs. 2 UStG '
                      'o. v. e. Auslagerer o. Lagerh. n. § 13a Abs. 1 Nr. 6 '
                      'UStG geschuldet werden (69)')}
        lines['66'] = {
            'code': '66', 'tax': 0.0,
            'name': _('Umsatzsteuer-Vorauszahlung')}
        lines['67'] = {
            'code': '67', 'tax': 0.0,
            'name': _('Abzug der festges. Sondervorauszahl. f. '
                      'Dauerfristverlängerung, nur auszuf. i. d. letzten '
                      'Voranmeldung d. Besteuerungszeitr., i.d.R. Dez. (39)')}

        return lines

    @api.model
    def _finalize_lines(self, lines):
        _26b = lines['26']['tax']
        _27b = lines['27']['tax']
        _28b = lines['28']['tax']
        _64b = lines['64']['tax']
        _65b = lines['65']['tax']

        # calculate lines 48 - 52
        lines['48']['tax'] = lines['48']['tax'] * 1
        _48b = lines['48']['tax']
        lines['49']['tax'] = lines['49']['tax'] * 1
        _49b = lines['49']['tax']
        lines['50']['tax'] = lines['50']['tax'] * 1
        _50b = lines['50']['tax']
        lines['51']['tax'] = lines['51']['tax'] * 1
        _51b = lines['51']['tax']
        lines['52']['tax'] = lines['52']['tax'] * 1
        _52b = lines['52']['tax']

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

        # calculate reverse of lines 48 - line 52 base
        lines['48']['base'] = lines['48']['base'] * -1
        lines['49']['base'] = lines['49']['base'] * -1
        lines['50']['base'] = lines['50']['base'] * -1
        lines['51']['base'] = lines['51']['base'] * -1
        lines['52']['base'] = lines['52']['base'] * -1

        # calculate reverse of line 55 - line 61
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
        lines['60']['tax'] = lines['60']['tax'] * -1
        _60b = lines['60']['tax']
        lines['61']['tax'] = lines['61']['tax'] * -1
        _61b = lines['61']['tax']

        # calculate line 53
        lines['53']['tax'] = lines['53']['tax'] * 1
        _53b = lines['53']['tax'] + _26b + _27b + _28b + _30b + _33b + _34b\
            + _35b + _36b + _48b + _49b + _50b + _51b + _52b

        # calculate line 62
        lines['62']['tax'] = lines['62']['tax'] * 1
        _62b = lines['62']['tax'] + _53b - _55b - _56b - _57b\
            - _58b - _59b - _60b - _61b

        # calculate line 66
        lines['66']['tax'] = lines['66']['tax'] * 1
        _66b = lines['66']['tax'] + _62b + _64b + _65b

        # update lines 53, 62, 66
        lines['66'].update({'tax': _66b})
        lines['53'].update({'tax': _53b})
        lines['62'].update({'tax': _62b})
        return lines

    @api.model
    def _get_tags_map(self):
        company_id = self.env.user.company_id.id
        config = self.env['l10n.de.tax.statement.config'].search([
            ('company_id', '=', company_id)], limit=1
        )
        if not config:
            raise UserError(
                _('Tags mapping not configured for this Company! '
                  'Check the DE Tags Configuration.'))
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
            config.tag_60_base.id: ('40', 'base'),
            config.tag_21_base.id: ('41', 'base'),
            config.tag_45_base.id: ('42', 'base'),
            config.tag_46_base.id: ('48', 'base'),
            config.tag_47_tax.id: ('48', 'tax'),
            config.tag_52_base.id: ('49', 'base'),
            config.tag_53_tax.id: ('49', 'tax'),
            config.tag_73_base.id: ('50', 'base'),
            config.tag_74_tax.id: ('50', 'tax'),
            config.tag_78_base.id: ('51', 'base'),
            config.tag_79_tax.id: ('51', 'tax'),
            config.tag_84_base.id: ('52', 'base'),
            config.tag_85_tax.id: ('52', 'tax'),
            config.tag_66_tax.id: ('55', 'tax'),
            config.tag_61_tax.id: ('56', 'tax'),
            config.tag_62_tax.id: ('57', 'tax'),
            config.tag_67_tax.id: ('58', 'tax'),
            config.tag_63_tax.id: ('59', 'tax'),
            config.tag_64_tax.id: ('60', 'tax'),
            config.tag_59_tax.id: ('61', 'tax'),
            config.tag_65_tax.id: ('64', 'tax'),
            config.tag_69_tax.id: ('65', 'tax'),
        }

    @api.multi
    def statement_update(self):
        self.ensure_one()

        if self.state in ['posted', 'final']:
            raise UserError(
                _('You cannot modify a posted statement!'))

        # clean old lines
        self.line_ids.unlink()

        # calculate lines
        lines = self._prepare_lines()
        taxes = self._compute_taxes()
        self._set_statement_lines(lines, taxes)
        taxes = self._compute_past_invoices_taxes()
        self._set_statement_lines(lines, taxes)
        self._finalize_lines(lines)

        # create lines
        for line in lines:
            lines[line].update({'statement_id': self.id})
            self.env['l10n.de.tax.statement.line'].create(
                lines[line]
            )
        self.date_update = fields.Datetime.now()

    def _compute_past_invoices_taxes(self):
        self.ensure_one()
        ctx = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'target_move': self.target_move,
            'company_id': self.company_id.id,
            'skip_invoice_basis_domain': True,
            'unreported_move': True,
            'unreported_move_from_date': self.unreported_move_from_date
        }
        taxes = self.env['account.tax'].with_context(ctx)
        for move in self.unreported_move_ids:
            for move_line in move.line_ids:
                if move_line.tax_exigible:
                    if move_line.tax_line_id:
                        taxes |= move_line.tax_line_id
        return taxes

    def _compute_taxes(self):
        self.ensure_one()
        ctx = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'target_move': self.target_move,
            'company_id': self.company_id.id,
        }
        domain = self._get_taxes_domain()
        taxes = self.env['account.tax'].with_context(ctx).search(domain)
        return taxes

    def _set_statement_lines(self, lines, taxes):
        self.ensure_one()
        tags_map = self._get_tags_map()
        for tax in taxes:
            for tag in tax.tag_ids:
                tag_map = tags_map.get(tag.id)
                if tag_map:
                    column = tag_map[1]
                    code = tag_map[0]
                    if column == 'base':
                        lines[code][column] += tax.base_balance
                    else:
                        lines[code][column] += tax.balance

    @api.multi
    def finalize(self):
        self.ensure_one()
        self.write({
            'state': 'final'
        })

    @api.multi
    def post(self):
        self.ensure_one()
        prev_open_statements = self.search([
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'draft'),
            ('id', '<', self.id)
        ], limit=1)

        if prev_open_statements:
            raise UserError(
                _('You cannot post a statement if all the previous '
                  'statements are not yet posted! '
                  'Please Post all the other statements first.'))

        self.write({
            'state': 'posted',
            'date_posted': fields.Datetime.now()
        })
        self.unreported_move_ids.write({
            'l10n_de_tax_statement_id': self.id,
        })
        domain = [
            ('company_id', '=', self.company_id.id),
            ('l10n_de_tax_statement_id', '=', False),
            ('date', '<=', self.to_date),
            ('date', '>=', self.from_date),
        ]
        move_line_ids = self.env['account.move.line'].search(domain)
        updated_move_ids = move_line_ids.mapped('move_id')
        updated_move_ids.write({
            'l10n_de_tax_statement_id': self.id,
        })

    @api.multi
    def reset(self):
        self.write({
            'state': 'draft',
            'date_posted': None
        })
        req = """
            UPDATE account_move_line
            SET l10n_de_tax_statement_id = NULL
            WHERE
              l10n_de_tax_statement_id = %s
        """
        self.env.cr.execute(
            req, (self.id, ))

    @api.model
    def _modifiable_values_when_posted(self):
        return ['state']

    @api.multi
    def write(self, values):
        for statement in self:
            if statement.state == 'final':
                raise UserError(
                    _('You cannot modify a statement set as final!'))
            if 'state' not in values or values['state'] != 'draft':
                if statement.state == 'posted':
                    for val in values:
                        if val not in self._modifiable_values_when_posted():
                            raise UserError(
                                _('You cannot modify a posted statement! '
                                  'Reset the statement to draft first.'))
        return super(VatStatement, self).write(values)

    @api.multi
    def unlink(self):
        for statement in self:
            if statement.state == 'posted':
                raise UserError(
                    _('You cannot delete a posted statement! '
                      'Reset the statement to draft first.'))
            if statement.state == 'final':
                raise UserError(
                    _('You cannot delete a statement set as final!'))
        super(VatStatement, self).unlink()

    @api.depends('line_ids.tax')
    def _compute_tax_total(self):
        for statement in self:
            total = 0.0
            for line in statement.line_ids:
                if line.code in ['66', '67']:
                    total += line.tax
            statement.tax_total = total
