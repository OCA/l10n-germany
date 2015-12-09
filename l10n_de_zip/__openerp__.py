# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{'name': 'Germany - Postal codes (ZIP) list',
 'summary': 'Provides all German postal codes for auto-completion',
 'version': '1.0.0',
 'depends': ['base', 'base_location','l10n_de_country_states'],
 'author': 'Camptocamp',
 'description': """
Germany postal code (ZIP) list
============================

This module will load all german postal codes (ZIP) in Odoo to
ease the input of partners.

It is not mandatory to use Odoo in Germany,
but can improve the user experience.

Zip codes are extract from Geonames files (http://www.geonames.org/)
""",
 'website': 'http://www.camptocamp.com',
 'data': ['data/l10n_de_zip.xml'],
 'demo_xml': [],
 'installable': True,
 'active': False}
