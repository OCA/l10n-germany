# Copyright (C) 2022-2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestGenerator(TransactionCase):
    def test_xml_generator(self):
        """Only test failing because other cases or covered in full tests"""
        root = etree.fromstring("<invalid/>")
        with self.assertRaises(UserError):
            self.env["datev.xml.generator"].check_xml_file("inv.xml", root)
