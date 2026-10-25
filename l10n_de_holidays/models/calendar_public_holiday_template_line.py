# Copyright 2018 elego Software Solutions GmbH - Yu Weng
# Copyright 2018 initOS GmbH - Nikolina Todorova
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date

from dateutil.relativedelta import SU, relativedelta

from odoo import fields, models


class CalendarPublicHolidayTemplateLine(models.Model):
    _inherit = "calendar.public.holiday.template.line"

    date_type = fields.Selection(
        selection_add=[("de_repentance_day", "Day of Repentance and Prayer")],
        ondelete={"de_repentance_day": "cascade"},
    )

    def _get_date_de_repentance_day(self, year):
        # Repentance Day is always 11 days before the first advent
        first_advent = date(year, 12, 24) + relativedelta(weekday=SU(-4))
        return first_advent + relativedelta(days=-11)
