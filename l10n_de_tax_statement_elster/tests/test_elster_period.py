# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.l10n_de_tax_statement_elster.services.period import (
    get_elster_period,
)


@tagged("-at_install", "post_install")
class TestElsterPeriod(BaseCommon):
    def _make_daterange(self, year, month, day, months=0):
        from_date = datetime.date(year, month, day)
        to_date = from_date + relativedelta(day=31, months=months)
        from calendar import monthrange

        last_day = monthrange(to_date.year, to_date.month)[1]
        to_date = to_date.replace(day=min(to_date.day, last_day))
        return from_date, to_date

    def _make_month(self, year, month):
        from calendar import monthrange

        return (
            datetime.date(year, month, 1),
            datetime.date(year, month, monthrange(year, month)[1]),
        )

    def _make_quarter(self, year, q):
        from calendar import monthrange

        start_month = (q - 1) * 3 + 1
        end_month = start_month + 2
        return (
            datetime.date(year, start_month, 1),
            datetime.date(year, end_month, monthrange(year, end_month)[1]),
        )

    def test_january_2026(self):
        f, t = self._make_month(2026, 1)
        code, ptype = get_elster_period(f, t)
        self.assertEqual(code, "01")
        self.assertEqual(ptype, "month")

    def test_december_2026(self):
        f, t = self._make_month(2026, 12)
        code, ptype = get_elster_period(f, t)
        self.assertEqual(code, "12")
        self.assertEqual(ptype, "month")

    def test_q1_2026(self):
        f, t = self._make_quarter(2026, 1)
        code, ptype = get_elster_period(f, t)
        self.assertEqual(code, "41")
        self.assertEqual(ptype, "quarter")

    def test_q4_2026(self):
        f, t = self._make_quarter(2026, 4)
        code, ptype = get_elster_period(f, t)
        self.assertEqual(code, "44")
        self.assertEqual(ptype, "quarter")

    def test_full_year_rejected(self):
        f, t = datetime.date(2026, 1, 1), datetime.date(2026, 12, 31)
        with self.assertRaises(UserError):
            get_elster_period(f, t)

    def test_incomplete_month_rejected(self):
        f, t = datetime.date(2026, 1, 5), datetime.date(2026, 1, 31)
        with self.assertRaises(UserError):
            get_elster_period(f, t)

    def test_incomplete_quarter_rejected(self):
        f, t = datetime.date(2026, 1, 5), datetime.date(2026, 3, 31)
        with self.assertRaises(UserError):
            get_elster_period(f, t)

    def test_year_transition_rejected(self):
        f, t = datetime.date(2026, 12, 1), datetime.date(2027, 1, 31)
        with self.assertRaises(UserError):
            get_elster_period(f, t)

    def test_other_year_rejected(self):
        f, t = self._make_month(2025, 6)
        with self.assertRaises(UserError):
            get_elster_period(f, t)

    def test_all_months_2026(self):
        for m in range(1, 13):
            f, t = self._make_month(2026, m)
            code, ptype = get_elster_period(f, t)
            self.assertEqual(ptype, "month")
            expected = f"{m:02d}"
            self.assertEqual(code, expected)

    def test_all_quarters_2026(self):
        for q in range(1, 5):
            f, t = self._make_quarter(2026, q)
            code, ptype = get_elster_period(f, t)
            self.assertEqual(ptype, "quarter")
            self.assertEqual(code, f"4{q}")
