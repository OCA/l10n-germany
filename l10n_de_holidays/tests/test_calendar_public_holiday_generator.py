# Copyright 2018 elego Software Solutions GmbH - Yu Weng
# Copyright 2018 initOS GmbH - Nikolina Todorova
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import UserError

from . import common


class TestCalendarPublicHolidayGenerator(common.TestHolidaysGenerator):
    def test_action_generate_de_holidays(self):
        self.calendar_public_holiday_generator.action_run()

        public_holiday = self.CalendarPublicHoliday.search(
            [("year", "=", self.TestYear), ("country_id", "=", self.CountryId)]
        )
        if not public_holiday:
            public_holiday = None

        self.assertIsNotNone(public_holiday)

        if public_holiday:
            line_ids = public_holiday.line_ids
            if not line_ids:
                line_ids = None
            self.assertIsNotNone(line_ids)

    def test_calculate_fixed_holidays(self):
        self.calendar_public_holiday_generator.action_run()

        public_holiday = self.CalendarPublicHoliday.search(
            [
                ("year", "=", self.TestYear),
                ("country_id", "=", self.CountryId),
            ]
        )
        self.assertTrue(public_holiday, "No public holiday created.")

        expected_dates = {
            date(self.TestYear, 1, 1),
            date(self.TestYear, 5, 1),
            date(self.TestYear, 10, 3),
            date(self.TestYear, 12, 25),
            date(self.TestYear, 12, 26),
        }

        fixed_dates = set(public_holiday.line_ids.mapped("date"))

        self.assertTrue(
            expected_dates.issubset(fixed_dates),
            f"Expected holidays: {expected_dates}, found: {fixed_dates}",
        )

        for line in public_holiday.line_ids:
            if line.date in expected_dates:
                self.assertFalse(
                    line.variable_date, f"{line.date} should not be variable date."
                )

    def test_action_copy_de_holidays(self):
        self.calendar_public_holiday_generator.action_generate_de_holidays()
        template_id = self.CalendarPublicHoliday.search(
            [("year", "=", self.TestYear), ("country_id", "=", self.CountryId)]
        )[0].id

        # Test Create Public Holidays for 2019 from 2019
        TestYear = 2019
        wizard_data = {
            "year": TestYear,
            "country_id": self.CountryId,
            "template_id": template_id,
        }

        calendar_public_holiday_generator_copy = (
            self.CalendarPublicHolidayGenerator.create(wizard_data)
        )

        calendar_public_holiday_generator_copy.action_run()

        public_holiday = self.CalendarPublicHoliday.search(
            [("year", "=", TestYear), ("country_id", "=", self.CountryId)]
        )
        if not public_holiday:
            public_holiday = None

        self.assertIsNotNone(public_holiday)

        if public_holiday:
            line_ids = public_holiday.line_ids
            if not line_ids:
                line_ids = None
            self.assertIsNotNone(line_ids)

    def test_copy_function_name_does_not_exists(self):
        self.calendar_public_holiday_generator.action_generate_de_holidays()
        template_id = self.CalendarPublicHoliday.search(
            [("year", "=", self.TestYear), ("country_id", "=", self.CountryId)]
        )[0].id

        # Test Create Public Holidays for 2019 from 2019
        # with not existing function for the CountryId
        CountryId = self.ref("base.fr")
        TestYear = 2019
        wizard_data = {
            "year": TestYear,
            "country_id": CountryId,
            "template_id": template_id,
        }
        calendar_public_holiday_generator_copy = (
            self.CalendarPublicHolidayGenerator.create(wizard_data)
        )

        with self.assertRaises(UserError):
            calendar_public_holiday_generator_copy.action_run()

    def test_generate_function_name_does_not_exists(self):
        # Test Generate Public Holidays for 2018
        # with not existing function for the CountryId
        CountryId = self.ref("base.fr")
        wizard_data = {"year": self.TestYear, "country_id": CountryId}
        calendar_public_holiday_generator_generate = (
            self.CalendarPublicHolidayGenerator.create(wizard_data)
        )

        with self.assertRaises(UserError):
            calendar_public_holiday_generator_generate.action_run()

    def test_copy_to_same_year_error(self):
        self.calendar_public_holiday_generator.action_generate_de_holidays()
        template_id = self.CalendarPublicHoliday.search(
            [("year", "=", self.TestYear), ("country_id", "=", self.CountryId)]
        )[0].id
        wizard_data = {
            "year": self.TestYear,
            "country_id": self.CountryId,
            "template_id": template_id,
        }
        calendar_public_holiday_generator_copy = (
            self.CalendarPublicHolidayGenerator.create(wizard_data)
        )

        with self.assertRaises(UserError):
            calendar_public_holiday_generator_copy.action_run()

    def test_calculate_repentance_day(self):
        # Repentance Day 2023 should be on 22.11.2023.
        result_2023 = self.calendar_public_holiday_generator.calculate_repentance_day(
            2023
        )
        self.assertTrue(result_2023, "No date calculated for 2023")
        self.assertEqual(result_2023, "2023-11-22")

        # Repentance Day 2023 should be on 20.11.2024.
        result_2024 = self.calendar_public_holiday_generator.calculate_repentance_day(
            2024
        )
        self.assertTrue(result_2024, "No date calculated for 2024")
        self.assertEqual(result_2024, "2024-11-20")

        # Repentance Day 2023 should be on 19.11.2025.
        result_2025 = self.calendar_public_holiday_generator.calculate_repentance_day(
            2025
        )
        self.assertTrue(result_2025, "No date calculated for 2025")
        self.assertEqual(result_2025, "2025-11-19")

    def test_generate_state_holidays(self):
        bavaria = self.env.ref("base.state_de_by")
        self.calendar_public_holiday_generator.state_id = bavaria
        self.calendar_public_holiday_generator.action_run()

        public_holiday = self.CalendarPublicHoliday.search(
            [("year", "=", self.TestYear), ("country_id", "=", self.CountryId)]
        )
        state_lines = public_holiday.line_ids.filtered("state_ids")
        self.assertIn(date(self.TestYear, 8, 15), state_lines.mapped("date"))
        self.assertIn(date(self.TestYear, 1, 6), state_lines.mapped("date"))
        self.assertIn(bavaria, state_lines.state_ids)
