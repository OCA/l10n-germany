# © 2024 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools import human_size


class DatevExportPackage(models.Model):
    _name = "datev.export.xml.line"
    _description = "DATEV XML Export Line"

    export_id = fields.Many2one("datev.export.xml", readonly=True)
    attachment_id = fields.Many2one("ir.attachment", ondelete="cascade", readonly=True)
    filename = fields.Char(readonly=True, related="attachment_id.name")
    filesize = fields.Char(compute="_compute_filesize")
    invoice_ids = fields.Many2many("account.move", readonly=True)
    invoices_count = fields.Integer(
        string="Invoices", compute="_compute_invoices_count", store=True
    )

    @api.depends("invoice_ids")
    def _compute_invoices_count(self):
        for line in self:
            line.invoices_count = len(line.invoice_ids)

    @api.depends("attachment_id", "attachment_id.file_size")
    def _compute_filesize(self):
        for line in self:
            line.filesize = human_size(line.attachment_id.file_size)

    def action_datev_download(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/datev/xml/download/{self.id}",
            "target": "self",
        }

    def action_open_invoices(self):
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
        if attachments:
            attachments.unlink()
        return super().unlink()
