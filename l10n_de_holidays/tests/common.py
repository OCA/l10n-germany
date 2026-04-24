#  Copyright 2018 elego Software Solutions GmbH - Yu Weng
#  Copyright 2018 initOS GmbH - Nikolina Todorova
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestHolidaysGenerator(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super(TestHolidaysGenerator, cls).setUpClass()

        # Usefull models
        cls.HrHolidaysPublicGenerator = cls.env["hr.holidays.public.generator"]
        cls.HrHolidaysPublicLine = cls.env["hr.holidays.public.line"]
        cls.HrHolidaysPublic = cls.env["hr.holidays.public"]
        cls.TestYear = 2018
        cls.CountryId = cls.env.ref("base.de").id

        # Test Create Public Holidays for 2018
        wizard_data = {"year": cls.TestYear, "country_id": cls.CountryId}
        cls.hr_holidays_public_generator = cls.HrHolidaysPublicGenerator.create(
            wizard_data
        )
