# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    query = """
        SELECT id, attachment_id FROM datev_export_xml
        WHERE attachment_id IS NOT NULL
    """
    env.cr.execute(query)

    for export_id, attachment_id in env.cr.fetchall():
        export = env["datev.export.xml"].browse(export_id)
        attachment = env["ir.attachment"].browse(attachment_id)

        _logger.info(f"Migrating attachment of {export}")

        line = export.line_ids.create(
            {
                "attachment_id": attachment_id,
                "export_id": export_id,
                "invoice_ids": [(6, 0, export.invoice_ids.ids)],
            }
        )

        attachment.write({"res_model": line._name, "res_id": line.id})
