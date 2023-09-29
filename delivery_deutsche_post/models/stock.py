from odoo import _, fields, models
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    label_de_attach_id = fields.Many2one(
        "ir.attachment", "Label Deutsche Post", copy=False
    )

    def get_deutsche_post_label(self):
        self.ensure_one()

        if self.label_de_attach_id:
            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/?model=ir.attachment&id="
                + str(self.label_de_attach_id.id)
                + "&field=datas&download=true&filename_field=name",
                "target": "download",
            }

        raise UserError(_("No DEPOST label found"))
