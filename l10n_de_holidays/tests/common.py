#  Copyright 2018 elego Software Solutions GmbH - Yu Weng
#  Copyright 2018 initOS GmbH - Nikolina Todorova
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestHolidaysGenerator(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Usefull models
        self.CalendarPublicHolidayGenerator = self.env[
            "calendar.public.holiday.generator"
        ]
        self.CalendarPublicHolidayLine = self.env["calendar.public.holiday.line"]
        self.CalendarPublicHoliday = self.env["calendar.public.holiday"]
        self.TestYear = 2018
        self.CountryId = self.ref("base.de")

        # Test Create Public Holidays for 2018
        wizard_data = {"year": self.TestYear, "country_id": self.CountryId}

        self.calendar_public_holiday_generator = (
            self.CalendarPublicHolidayGenerator.create(wizard_data)
        )
