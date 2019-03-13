# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tools import convert_file
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestVatStatement(TransactionCase):

    def _load(self, module, *args):
        convert_file(
            self.cr,
            'l10n_de',
            get_module_resource(module, *args),
            {}, 'init', False, 'test', self.registry._assertion_report)

    def setUp(self):
        super().setUp()

        self.Wizard = self.env['l10n.de.tax.statement.config.wizard']

        self.tag_1 = self.env['account.account.tag'].create({
            'name': 'Tag 1',
            'applicability': 'taxes',
        })
        self.tag_2 = self.env['account.account.tag'].create({
            'name': 'Tag 2',
            'applicability': 'taxes',
        })
        self.tag_3 = self.env['account.account.tag'].create({
            'name': 'Tag 3',
            'applicability': 'taxes',
        })
        self.tag_4 = self.env['account.account.tag'].create({
            'name': 'Tag 4',
            'applicability': 'taxes',
        })

        self.tax_1 = self.env['account.tax'].create({
            'name': 'Tax 1',
            'amount': 19,
            'tag_ids': [(6, 0, [self.tag_1.id])],
        })

        self.tax_2 = self.env['account.tax'].create({
            'name': 'Tax 2',
            'amount': 7,
            'tag_ids': [(6, 0, [self.tag_2.id])],
        })

        self.config = self.env['l10n.de.tax.statement.config'].create({
            'company_id': self.env.user.company_id.id,
            'tag_81_base': self.tag_1.id,
            'tag_86_base': self.tag_2.id,
            'tag_41_base': self.tag_3.id,
            'tag_21_base': self.tag_4.id,
        })

        daterange_type = self.env['date.range.type'].create({
            'name': 'Type 1'
        })

        self.daterange_1 = self.env['date.range'].create({
            'name': 'Daterange 1',
            'type_id': daterange_type.id,
            'date_start': '2016-01-01',
            'date_end': '2016-12-31',
        })

        self.statement_1 = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 1',
        })

        self.journal_1 = self.env['account.journal'].create({
            'name': 'Journal 1',
            'code': 'Jou1',
            'type': 'sale',
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Test partner'})

        type_account = self.env.ref('account.data_account_type_receivable')

        account_receivable = self.env['account.account'].search([
            ('user_type_id', '=', type_account.id)
        ], limit=1)

        invoice1_vals = [{
            'name': 'Test line',
            'quantity': 1.0,
            'account_id': account_receivable.id,
            'price_unit': 100.0,
            'invoice_line_tax_ids': [(6, 0, [self.tax_1.id])],
        }, {
            'name': 'Test line 2',
            'quantity': 1.0,
            'account_id': account_receivable.id,
            'price_unit': 50.0,
            'invoice_line_tax_ids': [(6, 0, [self.tax_2.id])],
        }]

        self.invoice_1 = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'name': 'ref1',
            'account_id': account_receivable.id,
            'journal_id': self.journal_1.id,
            'date_invoice': fields.Date.today(),
            'type': 'out_invoice',
            'invoice_line_ids': [(0, 0, value) for value in invoice1_vals]
        })

    def test_01_onchange(self):
        self.statement_1.write({'date_range_id': self.daterange_1.id})
        self.statement_1.onchange_date_range_id()
        self.assertEqual(self.statement_1.from_date, '2016-01-01')
        self.assertEqual(self.statement_1.to_date, '2016-12-31')

        self.statement_1.onchange_date()
        check_name = self.statement_1.company_id.name
        check_name += ': ' + ' '.join(
            [self.statement_1.from_date, self.statement_1.to_date])
        self.assertEqual(self.statement_1.name, check_name)

        self.statement_1.onchange_date_from_date()
        d_from = fields.Date.from_string(self.statement_1.from_date)
        # by default the unreported_move_from_date is set to
        # a quarter (three months) before the from_date of the statement
        d_from_2months = d_from + relativedelta(months=-3, day=1)
        new_date = fields.Date.to_string(d_from_2months)
        self.assertEqual(self.statement_1.unreported_move_from_date, new_date)

        self.assertEqual(self.statement_1.tax_total, 0.)

    def test_02_post_final(self):
        # in draft
        self.assertEqual(self.statement_1.state, 'draft')
        self.statement_1.statement_update()
        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())

        # first post
        self.statement_1.statement_update()
        self.statement_1.post()
        self.assertEqual(self.statement_1.state, 'posted')
        self.assertTrue(self.statement_1.date_posted)

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())

        # then finalize
        self.statement_1.finalize()
        self.assertEqual(self.statement_1.state, 'final')
        self.assertTrue(self.statement_1.date_posted)

        with self.assertRaises(UserError):
            self.statement_1.write({'name': 'Test Name Modified'})
        with self.assertRaises(UserError):
            self.statement_1.write({'state': 'posted'})
        with self.assertRaises(UserError):
            self.statement_1.write({'date_posted': fields.Datetime.now()})
        with self.assertRaises(UserError):
            self.statement_1.unlink()
        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
            with self.assertRaises(UserError):
                line.unlink()

        self.assertEqual(self.statement_1.tax_total, 0.)

    def test_03_reset(self):
        self.statement_1.reset()
        self.assertEqual(self.statement_1.state, 'draft')
        self.assertFalse(self.statement_1.date_posted)

        self.assertEqual(self.statement_1.tax_total, 0.)

        self.statement_1.statement_update()
        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())

    def test_04_write(self):
        self.statement_1.post()
        with self.assertRaises(UserError):
            self.statement_1.write({'name': 'Test Name'})

        self.assertEqual(self.statement_1.tax_total, 0.)

    def test_05_unlink_exception(self):
        self.statement_1.post()
        with self.assertRaises(UserError):
            self.statement_1.unlink()

    def test_06_unlink_working(self):
        self.statement_1.unlink()

    def test_07_update_exception1(self):
        self.statement_1.post()
        with self.assertRaises(UserError):
            self.statement_1.statement_update()

    def test_08_update_exception2(self):
        self.config.unlink()
        with self.assertRaises(UserError):
            self.statement_1.statement_update()

    def test_09_update_working(self):
        self.invoice_1._onchange_invoice_line_ids()
        self.invoice_1.action_invoice_open()
        self.statement_1.statement_update()
        self.assertEqual(len(self.statement_1.line_ids.ids), 47)

        _25 = self.statement_1.line_ids.filtered(lambda r: r.code == '25')
        _26 = self.statement_1.line_ids.filtered(lambda r: r.code == '26')
        _27 = self.statement_1.line_ids.filtered(lambda r: r.code == '27')

        self.assertEqual(len(_25), 1)
        self.assertEqual(len(_26), 1)
        self.assertEqual(len(_27), 1)

        self.assertFalse(_25.format_base)
        self.assertFalse(_25.format_tax)
        self.assertTrue(_25.is_group)
        self.assertTrue(_25.is_readonly)

        self.assertEqual(_26.format_base, '100.00')
        self.assertFalse(_26.is_group)
        self.assertFalse(_26.is_readonly)

        self.assertEqual(_27.format_base, '50.00')
        self.assertFalse(_27.is_group)
        self.assertFalse(_27.is_readonly)

        self.assertEqual(self.statement_1.tax_total, 22.5)
        self.assertEqual(self.statement_1.format_tax_total, '22.50')

    def test_10_line_unlink_exception(self):
        self.assertEqual(len(self.statement_1.line_ids.ids), 0)
        self.assertEqual(self.statement_1.tax_total, 0.)

        self.invoice_1.action_invoice_open()
        self.statement_1.statement_update()
        self.statement_1.post()
        with self.assertRaises(UserError):
            self.statement_1.line_ids.unlink()

        self.assertEqual(len(self.statement_1.line_ids.ids), 47)
        self.assertEqual(self.statement_1.tax_total, 22.5)

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
            self.assertTrue(line.is_readonly)
            with self.assertRaises(UserError):
                line.unlink()

    def test_11_wizard_execute(self):
        wizard = self.Wizard.create({})

        self.assertEqual(wizard.tag_81_base, self.tag_1)
        self.assertEqual(wizard.tag_86_base, self.tag_2)

        wizard.write({
            'tag_81_base': self.tag_1.id,
            'tag_86_base': self.tag_2.id,
        })

        self.config.unlink()

        wizard_2 = self.Wizard.create({})
        self.assertNotEqual(wizard_2.tag_81_base, self.tag_1)
        self.assertNotEqual(wizard_2.tag_86_base, self.tag_2)

        config = self.env['l10n.de.tax.statement.config'].search(
            [('company_id', '=', self.env.user.company_id.id)],
            limit=1)
        self.assertFalse(config)

        wizard.execute()

        config = self.env['l10n.de.tax.statement.config'].search(
            [('company_id', '=', self.env.user.company_id.id)],
            limit=1)
        self.assertTrue(config)
        self.assertEqual(config.tag_81_base, self.tag_1)
        self.assertEqual(config.tag_86_base, self.tag_2)

        self.assertEqual(self.statement_1.tax_total, 0.)

    def test_12_undeclared_invoice(self):
        self.invoice_1._onchange_invoice_line_ids()
        self.invoice_1.action_invoice_open()
        self.invoice_1.move_id.add_move_in_statement()
        for line in self.invoice_1.move_id.line_ids:
            self.assertTrue(line.l10n_de_tax_statement_include)
        self.invoice_1.move_id.unlink_move_from_statement()
        for line in self.invoice_1.move_id.line_ids:
            self.assertFalse(line.l10n_de_tax_statement_include)

        self.statement_1.statement_update()
        self.assertEqual(len(self.statement_1.line_ids.ids), 47)

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
        self.statement_1.post()
        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())

        invoice2 = self.invoice_1.copy()
        invoice2._onchange_invoice_line_ids()
        invoice2.action_invoice_open()
        statement2 = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 2',
        })
        statement2.statement_update()
        statement2.unreported_move_from_date = fields.Date.today()
        statement2.onchange_unreported_move_from_date()
        self.assertFalse(statement2.unreported_move_ids)

        self.assertEqual(self.statement_1.tax_total, 22.5)
        self.assertEqual(self.statement_1.format_tax_total, '22.50')

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
            self.assertTrue(line.is_readonly)

    def test_13_no_previous_statement_posted(self):
        statement2 = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 2',
        })
        statement2.statement_update()
        with self.assertRaises(UserError):
            statement2.post()

        self.assertEqual(self.statement_1.tax_total, 0.)
        self.assertEqual(self.statement_1.format_tax_total, '0.00')

        for line in self.statement_1.line_ids:
            self.assertTrue(line.view_base_lines())
            self.assertTrue(line.view_tax_lines())
            self.assertFalse(line.is_readonly)
