# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.addons.base.tests.common import BaseCommon


class TestCalendarPublicHolidayTemplateDe(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env.ref(
            "l10n_de_holidays.calendar_public_holiday_template_de"
        )
        cls.bavaria = cls.env.ref("base.state_de_by")
        cls.saxony = cls.env.ref("base.state_de_sn")

    def _get_dates(self, public_holiday, states=None):
        lines = public_holiday.line_ids.filtered(
            lambda line: line.state_ids == (states or line.state_ids.browse())
        )
        return set(lines.mapped("date"))

    def test_generate_2018(self):
        public_holiday = self.template.create_public_holidays(2018)
        self.assertEqual(public_holiday.country_id, self.env.ref("base.de"))
        self.assertEqual(
            self._get_dates(public_holiday),
            {
                date(2018, 1, 1),
                date(2018, 3, 30),
                date(2018, 4, 1),
                date(2018, 4, 2),
                date(2018, 5, 1),
                date(2018, 5, 10),
                date(2018, 5, 21),
                date(2018, 10, 3),
                date(2018, 12, 25),
                date(2018, 12, 26),
            },
        )
        lines = public_holiday.line_ids
        self.assertFalse(
            lines.filtered(lambda line: line.date == date(2018, 1, 1)).variable_date
        )
        self.assertTrue(
            lines.filtered(lambda line: line.date == date(2018, 4, 1)).variable_date
        )
        bavaria_dates = set(
            lines.filtered(lambda line: self.bavaria in line.state_ids).mapped("date")
        )
        self.assertEqual(
            bavaria_dates,
            {
                date(2018, 1, 6),
                date(2018, 5, 31),
                date(2018, 8, 15),
                date(2018, 11, 1),
            },
        )

    def test_repentance_day(self):
        for year, expected in (
            (2023, date(2023, 11, 22)),
            (2024, date(2024, 11, 20)),
            (2025, date(2025, 11, 19)),
        ):
            public_holiday = self.template.create_public_holidays(year)
            self.assertEqual(
                self._get_dates(public_holiday, self.saxony),
                {expected},
            )
