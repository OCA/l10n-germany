# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2019 sewisoft (sewisoft.de)
# Copyright (C) 2010-2023 big-consulting GmbH (www.openbig.de)
# Copyright (C) 2010 OpenGLOBE Grzegorz Grzelak (www.openglobe.pl)
# @author Guenter Selbert <guenter.selbert@sewisoft.de>
# @author Thorsten Vocks
# @author Grzegorz Grzelak
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DatevExport(models.Model):
    _name = "datev.export.xml"
    _inherit = ["mail.thread", "mail.activity.mixin", "datev.zip.generator"]
    _description = "DATEV XML Export"

    @api.model
    def _default_start(self, today=None):
        today = today or datetime.date.today()
        default_period = self.env.company.datev_default_period
        if default_period == "week":
            return today - datetime.timedelta(days=today.weekday(), weeks=1)

        if default_period == "month":
            date = datetime.date(day=1, month=today.month, year=today.year)
            date_stop = date - datetime.timedelta(days=1)
            return datetime.date(day=1, month=date_stop.month, year=date_stop.year)

        if default_period == "year":
            return datetime.date(day=1, month=1, year=today.year - 1)

        return today - datetime.timedelta(days=1)

    @api.model
    def _default_stop(self, today=None):
        today = today or datetime.date.today()
        default_period = self.env.company.datev_default_period

        if default_period == "week":
            date_start = today - datetime.timedelta(days=today.weekday(), weeks=1)
            return date_start + datetime.timedelta(days=6)

        if default_period == "month":
            date = datetime.date(day=1, month=today.month, year=today.year)
            return date - datetime.timedelta(days=1)

        if default_period == "year":
            return datetime.date(day=31, month=12, year=today.year - 1)

        return today - datetime.timedelta(days=1)

    def name_get(self):
        return [(r.id, f"{r.create_date} {r.create_uid.name}") for r in self]

    name = fields.Char()
    export_type = fields.Selection(
        [("out", _("Customers")), ("in", _("Vendors"))],
        default="out",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    export_invoice = fields.Boolean(
        string="Export Invoices",
        default=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    export_refund = fields.Boolean(
        string="Export Refunds",
        default=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_start = fields.Date(
        string="From Date",
        default=_default_start,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_stop = fields.Date(
        string="To Date",
        default=_default_stop,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    client_number = fields.Char(related="company_id.datev_client_number", readonly=True)
    consultant_number = fields.Char(
        related="company_id.datev_consultant_number", readonly=True
    )
    check_xsd = fields.Boolean(
        string="Check XSD",
        required=True,
        default=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    line_ids = fields.One2many(
        "datev.export.xml.line",
        "export_id",
        "Lines",
    )
    line_count = fields.Integer(compute="_compute_line_count")

    problematic_invoices_count = fields.Integer(
        compute="_compute_problematic_invoices_count"
    )
    invoice_ids = fields.Many2many(comodel_name="account.move", string="Invoices")
    invoices_count = fields.Integer(
        string="Total Invoices", compute="_compute_invoices_count", store=True
    )
    invoices_exported_count = fields.Integer(
        string="Exported Invoices", compute="_compute_invoices_count", store=True
    )

    manually_document_selection = fields.Boolean(default=False)
    exception_info = fields.Text(string="Exception Info", readonly=True)

    state = fields.Selection(
        [
            ("draft", _("Draft")),
            ("pending", _("Pending")),
            ("running", _("Running")),
            ("done", _("Done")),
            ("failed", _("Failed")),
        ],
        string="Status",
        default="draft",
        required=True,
        readonly=True,
        tracking=True,
    )

    @api.depends("line_ids")
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.depends("invoice_ids")
    def _compute_problematic_invoices_count(self):
        for rec in self:
            rec.problematic_invoices_count = len(
                rec.invoice_ids.filtered("datev_validation")
            )

    @api.depends("invoice_ids", "line_ids", "line_ids.invoice_ids")
    def _compute_invoices_count(self):
        for rec in self:
            rec.invoices_count = len(rec.invoice_ids)
            rec.invoices_exported_count = len(rec.mapped("line_ids.invoice_ids"))

    @api.constrains("export_invoice", "export_refund", "export_type")
    def validate_types(self):
        if self.manually_document_selection:
            return
        if not self.export_type:
            raise ValidationError(
                _("You need to choose an export type (Customer/Vendor)!")
            )
        if not self.export_invoice and not self.export_refund:
            raise ValidationError(
                _(
                    "You need to choose which documents types (Invoices/Refunds) "
                    "you want to export!"
                )
            )

    def get_type_list(self):
        list_invoice_type = []
        if self.export_type:
            if self.export_invoice:
                list_invoice_type.append(self.export_type + "_invoice")
            if self.export_refund:
                list_invoice_type.append(self.export_type + "_refund")

        if not list_invoice_type:
            raise UserError(
                _("Missing Data\nPlease choose which documents you want to export!")
            )
        return list_invoice_type

    def get_invoices(self):
        list_invoice_type = self.get_type_list()
        search_clause = [
            ("amount_untaxed", "!=", 0),
            ("amount_total", "!=", 0),
            ("state", "in", ("posted", "open")),
            ("move_type", "in", list_invoice_type),
            ("company_id", "=", self.company_id.id),
        ]
        if self.company_id.datev_export_state:
            search_clause.append(("datev_exported", "=", False))
        if self.date_start:
            search_clause.append(("invoice_date", ">=", self.date_start))
            if self.date_stop:
                search_clause.append(("invoice_date", "<=", self.date_stop))
        else:
            raise UserError(
                _("Data Insufficient!\nPlease select Period or at least Start Date.")
            )
        return self.env["account.move"].search(search_clause)

    def _get_zip(self):
        generator = self.generate_zip(
            self.invoice_ids - self.mapped("line_ids.invoice_ids"),
            self.check_xsd,
        )

        for index, (zip_file, invoices) in enumerate(generator, 1):
            if not self.manually_document_selection:
                description = _(
                    "Filtered Export of %(count)s Documents\n"
                    "Date Range: %(start)s-%(stop)s\nTypes: %(types)s",
                    count=len(invoices),
                    start=self.date_start,
                    stop=self.date_stop,
                    types=", ".join(self.get_type_list()),
                )
            else:
                description = _(
                    "Manual Export of %(count)s Documents\n" "Numbers: %(names)s",
                    count=len(invoices),
                    names=", ".join(self.invoice_ids.mapped("name")),
                )

            attachment = self.env["ir.attachment"].create(
                {
                    "name": time.strftime(f"%Y-%m-%d_%H%M-{index}.zip"),
                    "datas": zip_file,
                    "res_model": "datev.export.xml",
                    "res_id": self.id,
                    "description": description,
                }
            )
            self.line_ids.sudo().create(
                {
                    "export_id": self.id,
                    "attachment_id": attachment.id,
                    "invoice_ids": [(6, 0, invoices.ids)],
                }
            )

            # Huge numbers of invoices can lead to cron timeouts. Commit after
            # each package and continue. When the timeout hits the job is still
            # in running and is set to pending in the cron (hanging job) and
            # will continue with the next package
            if self.env.context.get("datev_autocommit"):
                # pylint: disable=invalid-commit
                self.env.cr.commit()

    def get_zip(self):
        self.ensure_one()

        try:
            self.write({"state": "running", "exception_info": None})
            self.with_context(bin_size=False)._get_zip()
            if self.invoices_count == self.invoices_exported_count:
                self.write({"state": "done"})
        except Exception as e:
            _logger.exception(e)
            msg = e.name if hasattr(e, "name") else str(e)
            self.write({"exception_info": msg, "state": "failed"})

        self._compute_problematic_invoices_count()

    @api.model
    def cron_run_pending_export(self):
        """
        A Cron job can't execute parallel, so if we run this cron and there is
        currently a running datev export we can restart it.
        """
        hanging_datev_exports = self.search(
            [("state", "=", "running"), ("manually_document_selection", "=", False)]
        )
        hanging_datev_exports.write({"state": "pending"})
        datev_export = self.search(
            [
                ("state", "in", ("running", "pending")),
                ("manually_document_selection", "=", False),
            ],
            # Favor hanging jobs
            order="state DESC",
            limit=1,
        )

        if not datev_export:
            return

        datev_export.with_user(datev_export.create_uid.id).with_context(
            datev_autocommit=True
        ).get_zip()

        if datev_export.state == "done":
            datev_export._create_activity()
            datev_export.invoice_ids.write({"datev_exported": True})

    def export_zip(self):
        self.ensure_one()
        if self.manually_document_selection:
            self.get_zip()
            if self.env.context.get("wizard"):
                return self._return_wizard_action()
        else:
            self.invoice_ids = [(6, 0, self.get_invoices().ids)]
            self.action_pending()

    @api.model
    def export_zip_invoice(self, invoice_ids=None):
        if not invoice_ids and self.env.context.get("active_model") == "account.move":
            invoice_ids = self.env.context.get("active_ids")

        invoices = self.env["account.move"].browse(invoice_ids)
        types = invoices.mapped("move_type")

        if all(x.startswith("in_") for x in types):
            export_type = "in"
        elif all(x.startswith("out_") for x in types):
            export_type = "out"
        else:
            raise UserError(
                _("You can't export incoming and outgoing invoices at the same time")
            )

        datev_export = self.create(
            {
                "invoice_ids": [(6, 0, invoice_ids)],
                "export_type": export_type,
                "manually_document_selection": True,
                "date_start": False,
                "date_stop": False,
            }
        )
        datev_export.get_zip()
        datev_export._create_activity()
        datev_export.invoice_ids.write({"datev_exported": True})
        return datev_export._return_wizard_action()

    def _return_wizard_action(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "view_id": self.env.ref("datev_export_xml.view_datev_export_popup_form").id,
            "res_id": self.id,
            "res_model": self._name,
            "target": "new",
            "context": {"default_model": self._name, "wizard": True},
        }

    def _create_activity(self):
        self.ensure_one()
        if self.state == "done":
            note = _("DATEV Export file is ready to download!")
        elif self.state == "failed":
            note = _("Exception while creating DATEV-Export file!")
        else:
            return
        self.env["mail.activity"].sudo().create(
            {
                "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                "note": note,
                "res_id": self.id,
                "res_model_id": self.env.ref(
                    "datev_export_xml.model_datev_export_xml"
                ).id,
                "user_id": self.create_uid.id,
            }
        )

    def action_invalidate_lines(self):
        self.line_ids.write({"invalidated": True})

    def action_validate(self):
        generator = self.env["datev.xml.generator"]
        for invoice in self.invoice_ids:
            try:
                generator.generate_xml_invoice(invoice)
            except UserError:
                pass

        self._compute_problematic_invoices_count()

    def action_done(self):
        self.filtered(lambda r: r.state in ["running", "failed"]).write(
            {
                "exception_info": _("Manually set to Done by %s!") % self.env.user,
                "state": "done",
            }
        )

    def action_pending(self):
        for r in self:
            if not r.manually_document_selection:
                r.invoice_ids = [(6, 0, r.get_invoices().ids)]
            if r.invoices_count == 0:
                raise ValidationError(_("No invoices/refunds for export!"))
            if r.state == "running":
                raise ValidationError(
                    _("It's not allowed to set an already running export to pending!")
                )
            r.write(
                {
                    "state": "pending",
                    "exception_info": None,
                }
            )

    def action_draft(self):
        if "running" in self.mapped("state"):
            raise ValidationError(
                _("It's not allowed to set a running export to draft!")
            )

        self.write({"state": "draft", "line_ids": [(5,)]})

    def action_show_invalid_invoices_view(self):
        tree_view = self.env.ref("datev_export_xml.view_move_datev_validation")
        return {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "views": [[tree_view.id, "tree"], [False, "form"]],
            "res_model": "account.move",
            "target": "current",
            "name": _("Problematic Invoices"),
            "domain": [("id", "in", self.invoice_ids.filtered("datev_validation").ids)],
        }

    def action_show_related_invoices_view(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "tree,kanban,form",
            "res_model": "account.move",
            "target": "current",
            "name": _("Included Invoices"),
            "domain": [("id", "in", self.invoice_ids.ids)],
        }

    def unlink(self):
        attachments = self.mapped("attachment_id")
        res = super().unlink()
        attachments.exists().unlink()
        return res

    def write(self, vals):
        res = super().write(vals)
        if any(
            r in vals
            for r in [
                "export_type",
                "export_invoice",
                "export_refund",
                "date_start",
                "date_stop",
            ]
        ):
            for r in self:
                if r.manually_document_selection:
                    continue

                super(DatevExport, r).write(
                    {"invoice_ids": [(6, 0, r.get_invoices().ids)]}
                )
        return res

    @api.model
    def create(self, vals):
        r = super().create(vals)
        if not r.manually_document_selection:
            r.invoice_ids = [(6, 0, r.get_invoices().ids)]
        return r
