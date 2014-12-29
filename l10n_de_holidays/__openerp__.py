# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2010-2013 OpenERP s.a. (<http://openerp.com>).
# Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
# Author Nikolina Todorova <nikolina.todorova@initos.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Public Holidays',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'author': 'initOS GmbH & Co. KG',
    'description': """
    Public Holidays in Germany
======================
    """,
    'website': '',
    'depends': [
        'hr_public_holidays',
        'l10n_de_country_states'
    ],
    'init_xml': [
    ],
    'update_xml': [
        'data/public_holidays.xml'
    ],
    'test': [
    ],
    'demo_xml': [

    ],
    'installable': True,
    'active': False,
}
