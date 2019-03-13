# Copyright 2019 BIG-Consulting GmbH (<http://www.openbig.org>)
# Copyright 2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class VatStatementConfigWizard(models.TransientModel):
    _name = 'l10n.de.tax.statement.config.wizard'
    _description = 'German Vat Statement Configuration Wizard'

    tag_41_base = fields.Many2one('account.account.tag')
    tag_44_base = fields.Many2one('account.account.tag')
    tag_49_base = fields.Many2one('account.account.tag')
    tag_43_base = fields.Many2one('account.account.tag')
    tag_48_base = fields.Many2one('account.account.tag')
    tag_81_base = fields.Many2one('account.account.tag')
    tag_86_base = fields.Many2one('account.account.tag')
    tag_35_base = fields.Many2one('account.account.tag')
    tag_36_tax = fields.Many2one('account.account.tag')
    tag_77_base = fields.Many2one('account.account.tag')
    tag_76_base = fields.Many2one('account.account.tag')
    tag_80_tax = fields.Many2one('account.account.tag')
    tag_91_base = fields.Many2one('account.account.tag')
    tag_89_base = fields.Many2one('account.account.tag')
    tag_93_base = fields.Many2one('account.account.tag')
    tag_95_base = fields.Many2one('account.account.tag')
    tag_98_tax = fields.Many2one('account.account.tag')
    tag_94_base = fields.Many2one('account.account.tag')
    tag_96_tax = fields.Many2one('account.account.tag')
    tag_42_base = fields.Many2one('account.account.tag')
    tag_68_base = fields.Many2one('account.account.tag')
    tag_60_base = fields.Many2one('account.account.tag')
    tag_21_base = fields.Many2one('account.account.tag')
    tag_45_base = fields.Many2one('account.account.tag')
    tag_46_base = fields.Many2one('account.account.tag')
    tag_47_tax = fields.Many2one('account.account.tag')
    tag_52_base = fields.Many2one('account.account.tag')
    tag_53_tax = fields.Many2one('account.account.tag')
    tag_73_base = fields.Many2one('account.account.tag')
    tag_74_tax = fields.Many2one('account.account.tag')
    tag_78_base = fields.Many2one('account.account.tag')
    tag_79_tax = fields.Many2one('account.account.tag')
    tag_84_base = fields.Many2one('account.account.tag')
    tag_85_tax = fields.Many2one('account.account.tag')
    tag_65_tax = fields.Many2one('account.account.tag')
    tag_66_tax = fields.Many2one('account.account.tag')
    tag_61_tax = fields.Many2one('account.account.tag')
    tag_62_tax = fields.Many2one('account.account.tag')
    tag_67_tax = fields.Many2one('account.account.tag')
    tag_63_tax = fields.Many2one('account.account.tag')
    tag_64_tax = fields.Many2one('account.account.tag')
    tag_59_tax = fields.Many2one('account.account.tag')
    tag_69_tax = fields.Many2one('account.account.tag')
    tag_83_tax = fields.Many2one('account.account.tag')

    @api.model
    def default_get(self, fields_list):
        defv = super(VatStatementConfigWizard, self).default_get(fields_list)

        company_id = self.env.user.company_id.id
        config = self.env['l10n.de.tax.statement.config'].search([
            ('company_id', '=', company_id)], limit=1
        )
        if config:
            defv.setdefault('tag_41_base', config.tag_41_base.id)
            defv.setdefault('tag_44_base', config.tag_44_base.id)
            defv.setdefault('tag_49_base', config.tag_49_base.id)
            defv.setdefault('tag_43_base', config.tag_43_base.id)
            defv.setdefault('tag_48_base', config.tag_48_base.id)
            defv.setdefault('tag_81_base', config.tag_81_base.id)
            defv.setdefault('tag_86_base', config.tag_86_base.id)
            defv.setdefault('tag_35_base', config.tag_35_base.id)
            defv.setdefault('tag_36_tax', config.tag_36_tax.id)
            defv.setdefault('tag_77_base', config.tag_77_base.id)
            defv.setdefault('tag_76_base', config.tag_76_base.id)
            defv.setdefault('tag_80_tax', config.tag_80_tax.id)
            defv.setdefault('tag_91_base', config.tag_91_base.id)
            defv.setdefault('tag_89_base', config.tag_89_base.id)
            defv.setdefault('tag_93_base', config.tag_93_base.id)
            defv.setdefault('tag_95_base', config.tag_95_base.id)
            defv.setdefault('tag_98_tax', config.tag_98_tax.id)
            defv.setdefault('tag_94_base', config.tag_94_base.id)
            defv.setdefault('tag_96_tax', config.tag_96_tax.id)
            defv.setdefault('tag_42_base', config.tag_42_base.id)
            defv.setdefault('tag_68_base', config.tag_68_base.id)
            defv.setdefault('tag_60_base', config.tag_60_base.id)
            defv.setdefault('tag_21_base', config.tag_21_base.id)
            defv.setdefault('tag_45_base', config.tag_45_base.id)
            defv.setdefault('tag_46_base', config.tag_46_base.id)
            defv.setdefault('tag_47_tax', config.tag_47_tax.id)
            defv.setdefault('tag_52_base', config.tag_52_base.id)
            defv.setdefault('tag_53_tax', config.tag_53_tax.id)
            defv.setdefault('tag_73_base', config.tag_73_base.id)
            defv.setdefault('tag_74_tax', config.tag_74_tax.id)
            defv.setdefault('tag_78_base', config.tag_78_base.id)
            defv.setdefault('tag_79_tax', config.tag_79_tax.id)
            defv.setdefault('tag_84_base', config.tag_84_base.id)
            defv.setdefault('tag_85_tax', config.tag_85_tax.id)
            defv.setdefault('tag_65_tax', config.tag_65_tax.id)
            defv.setdefault('tag_66_tax', config.tag_66_tax.id)
            defv.setdefault('tag_61_tax', config.tag_61_tax.id)
            defv.setdefault('tag_62_tax', config.tag_62_tax.id)
            defv.setdefault('tag_67_tax', config.tag_67_tax.id)
            defv.setdefault('tag_63_tax', config.tag_63_tax.id)
            defv.setdefault('tag_64_tax', config.tag_64_tax.id)
            defv.setdefault('tag_59_tax', config.tag_59_tax.id)
            defv.setdefault('tag_69_tax', config.tag_69_tax.id)
            return defv

        if not (self.is_l10n_de_coa_skr03() or self.is_l10n_de_coa_skr04()):
            return defv

        defv.setdefault('tag_41_base', self.env.ref('l10n_de.tag_de_41').id)
        defv.setdefault('tag_44_base', self.env.ref('l10n_de.tag_de_44').id)
        defv.setdefault('tag_49_base', self.env.ref('l10n_de.tag_de_49').id)
        defv.setdefault('tag_43_base', self.env.ref('l10n_de.tag_de_43').id)
        defv.setdefault('tag_48_base', self.env.ref('l10n_de.tag_de_48').id)
        defv.setdefault('tag_81_base', self.env.ref('l10n_de.tag_de_81').id)
        defv.setdefault('tag_86_base', self.env.ref('l10n_de.tag_de_86').id)
        defv.setdefault('tag_35_base', self.env.ref('l10n_de.tag_de_35').id)
        defv.setdefault('tag_36_tax', self.env.ref('l10n_de.tag_de_36').id)
        defv.setdefault('tag_77_base', self.env.ref('l10n_de.tag_de_77').id)
        defv.setdefault('tag_76_base', self.env.ref('l10n_de.tag_de_76').id)
        defv.setdefault('tag_80_tax', self.env.ref('l10n_de.tag_de_80').id)
        defv.setdefault('tag_91_base', self.env.ref('l10n_de.tag_de_91').id)
        defv.setdefault('tag_89_base', self.env.ref('l10n_de.tag_de_89').id)
        defv.setdefault('tag_93_base', self.env.ref('l10n_de.tag_de_93').id)
        defv.setdefault('tag_95_base', self.env.ref('l10n_de.tag_de_95').id)
        defv.setdefault('tag_98_tax', self.env.ref('l10n_de.tag_de_98').id)
        defv.setdefault('tag_94_base', self.env.ref('l10n_de.tag_de_94').id)
        defv.setdefault('tag_96_tax', self.env.ref('l10n_de.tag_de_96').id)
        defv.setdefault('tag_42_base', self.env.ref('l10n_de.tag_de_42').id)
        defv.setdefault('tag_68_base', self.env.ref('l10n_de.tag_de_68').id)
        defv.setdefault('tag_60_base', self.env.ref('l10n_de.tag_de_60').id)
        defv.setdefault('tag_21_base', self.env.ref('l10n_de.tag_de_21').id)
        defv.setdefault('tag_45_base', self.env.ref('l10n_de.tag_de_45').id)
        defv.setdefault('tag_46_base', self.env.ref('l10n_de.tag_de_46').id)
        defv.setdefault('tag_47_tax', self.env.ref('l10n_de.tag_de_47').id)
        defv.setdefault('tag_52_base', self.env.ref('l10n_de.tag_de_52').id)
        defv.setdefault('tag_53_tax', self.env.ref('l10n_de.tag_de_53').id)
        defv.setdefault('tag_73_base', self.env.ref('l10n_de.tag_de_73').id)
        defv.setdefault('tag_74_tax', self.env.ref('l10n_de.tag_de_74').id)
        defv.setdefault('tag_78_base', self.env.ref('l10n_de.tag_de_78').id)
        defv.setdefault('tag_79_tax', self.env.ref('l10n_de.tag_de_79').id)
        defv.setdefault('tag_84_base', self.env.ref('l10n_de.tag_de_84').id)
        defv.setdefault('tag_85_tax', self.env.ref('l10n_de.tag_de_85').id)
        defv.setdefault('tag_65_tax', self.env.ref('l10n_de.tag_de_65').id)
        defv.setdefault('tag_66_tax', self.env.ref('l10n_de.tag_de_66').id)
        defv.setdefault('tag_61_tax', self.env.ref('l10n_de.tag_de_61').id)
        defv.setdefault('tag_62_tax', self.env.ref('l10n_de.tag_de_62').id)
        defv.setdefault('tag_67_tax', self.env.ref('l10n_de.tag_de_67').id)
        defv.setdefault('tag_63_tax', self.env.ref('l10n_de.tag_de_63').id)
        defv.setdefault('tag_64_tax', self.env.ref('l10n_de.tag_de_64').id)
        defv.setdefault('tag_59_tax', self.env.ref('l10n_de.tag_de_59').id)
        defv.setdefault('tag_69_tax', self.env.ref('l10n_de.tag_de_69').id)
        return defv

    def is_l10n_de_coa_skr03(self):
        is_l10n_de_coa_skr03 = self.env.ref(
            'l10n_de_skr03.l10n_de_chart_template', False)
        company_coa = self.env.user.company_id.chart_template_id
        return company_coa == is_l10n_de_coa_skr03

    def is_l10n_de_coa_skr04(self):
        is_l10n_de_coa_skr04 = self.env.ref(
            'l10n_de_skr04.l10n_chart_de_skr04', False)
        company_coa = self.env.user.company_id.chart_template_id
        return company_coa == is_l10n_de_coa_skr04

    @api.multi
    def execute(self):
        self.ensure_one()

        company_id = self.env.user.company_id.id
        config = self.env['l10n.de.tax.statement.config'].search([
            ('company_id', '=', company_id)], limit=1
        )
        if not config:
            config = self.env['l10n.de.tax.statement.config'].create({
                'company_id': company_id
            })
        config.write({
            'company_id': company_id,
            'tag_41_base': self.tag_41_base.id,
            'tag_44_base': self.tag_44_base.id,
            'tag_49_base': self.tag_49_base.id,
            'tag_43_base': self.tag_43_base.id,
            'tag_48_base': self.tag_48_base.id,
            'tag_81_base': self.tag_81_base.id,
            'tag_86_base': self.tag_86_base.id,
            'tag_35_base': self.tag_35_base.id,
            'tag_36_tax': self.tag_36_tax.id,
            'tag_77_base': self.tag_77_base.id,
            'tag_76_base': self.tag_76_base.id,
            'tag_80_tax': self.tag_80_tax.id,
            'tag_91_base': self.tag_91_base.id,
            'tag_89_base': self.tag_89_base.id,
            'tag_93_base': self.tag_93_base.id,
            'tag_95_base': self.tag_95_base.id,
            'tag_98_tax': self.tag_98_tax.id,
            'tag_94_base': self.tag_94_base.id,
            'tag_96_tax': self.tag_96_tax.id,
            'tag_42_base': self.tag_42_base.id,
            'tag_68_base': self.tag_68_base.id,
            'tag_60_base': self.tag_60_base.id,
            'tag_21_base': self.tag_21_base.id,
            'tag_45_base': self.tag_45_base.id,
            'tag_46_base': self.tag_46_base.id,
            'tag_47_tax': self.tag_47_tax.id,
            'tag_52_base': self.tag_52_base.id,
            'tag_53_tax': self.tag_53_tax.id,
            'tag_73_base': self.tag_73_base.id,
            'tag_74_tax': self.tag_74_tax.id,
            'tag_78_base': self.tag_78_base.id,
            'tag_79_tax': self.tag_79_tax.id,
            'tag_84_base': self.tag_84_base.id,
            'tag_85_tax': self.tag_85_tax.id,
            'tag_65_tax': self.tag_65_tax.id,
            'tag_66_tax': self.tag_66_tax.id,
            'tag_61_tax': self.tag_61_tax.id,
            'tag_62_tax': self.tag_62_tax.id,
            'tag_67_tax': self.tag_67_tax.id,
            'tag_63_tax': self.tag_63_tax.id,
            'tag_64_tax': self.tag_64_tax.id,
            'tag_59_tax': self.tag_59_tax.id,
            'tag_69_tax': self.tag_69_tax.id,
        })

        action_name = 'l10n_de_tax_statement.action_account_tax_statement_de'
        action = self.env.ref(action_name).read()[0]
        return action
