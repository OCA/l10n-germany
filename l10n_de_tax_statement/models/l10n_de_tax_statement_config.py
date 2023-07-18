# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class VatStatementConfig(models.Model):
    _name = 'l10n.de.tax.statement.config'

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True
    )

    tag_21_base = fields.Many2one('account.account.tag')
    tag_35_base = fields.Many2one('account.account.tag')
    tag_36_tax = fields.Many2one('account.account.tag')
    tag_41_base = fields.Many2one('account.account.tag')
    tag_42_base = fields.Many2one('account.account.tag')
    tag_43_base = fields.Many2one('account.account.tag')
    tag_44_base = fields.Many2one('account.account.tag')
    tag_45_base = fields.Many2one('account.account.tag')
    tag_46_base = fields.Many2one('account.account.tag')
    tag_47_tax = fields.Many2one('account.account.tag')
    tag_48_base = fields.Many2one('account.account.tag')
    tag_49_base = fields.Many2one('account.account.tag')
    tag_52_base = fields.Many2one('account.account.tag')
    tag_53_tax = fields.Many2one('account.account.tag')
    tag_59_tax = fields.Many2one('account.account.tag')
    tag_60_base = fields.Many2one('account.account.tag')
    tag_61_tax = fields.Many2one('account.account.tag')
    tag_62_tax = fields.Many2one('account.account.tag')
    tag_63_tax = fields.Many2one('account.account.tag')
    tag_64_tax = fields.Many2one('account.account.tag')
    tag_65_tax = fields.Many2one('account.account.tag')
    tag_66_tax = fields.Many2one('account.account.tag')
    tag_67_tax = fields.Many2one('account.account.tag')
    tag_68_base = fields.Many2one('account.account.tag')
    tag_69_tax = fields.Many2one('account.account.tag')
    tag_73_base = fields.Many2one('account.account.tag')
    tag_74_tax = fields.Many2one('account.account.tag')
    tag_76_base = fields.Many2one('account.account.tag')
    tag_77_base = fields.Many2one('account.account.tag')
    tag_78_base = fields.Many2one('account.account.tag')
    tag_79_tax = fields.Many2one('account.account.tag')
    tag_80_tax = fields.Many2one('account.account.tag')
    tag_81_base = fields.Many2one('account.account.tag')
    tag_81_tax = fields.Many2one('account.account.tag')
    tag_84_base = fields.Many2one('account.account.tag')
    tag_85_tax = fields.Many2one('account.account.tag')
    tag_86_base = fields.Many2one('account.account.tag')
    tag_86_tax = fields.Many2one('account.account.tag')
    tag_89_base = fields.Many2one('account.account.tag')
    tag_89_tax = fields.Many2one('account.account.tag')
    tag_91_base = fields.Many2one('account.account.tag')
    tag_93_base = fields.Many2one('account.account.tag')
    tag_93_tax = fields.Many2one('account.account.tag')
    tag_94_base = fields.Many2one('account.account.tag')
    tag_95_base = fields.Many2one('account.account.tag')
    tag_96_tax = fields.Many2one('account.account.tag')
    tag_98_tax = fields.Many2one('account.account.tag')
