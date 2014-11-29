# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2013 OpenERP s.a. (<http://openerp.com>).
#    Copyright (C) 2014 copado MEDIA UG (<http://www.copado.de>).
#    Author Mathias Neef <mn[at]copado.de>
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
{
    'name': 'eCommerce German additions',
    'category': 'Website',
    'summary': 'German additions for eCommerce (B2C)',
    'version': '1.0',
    'description': """
German additions for eCommerce (B2C)
==========================

This addon installes necessary additions in accordance with statutory requirements in Germany.

Overview
--------
 - adds terms page
 - adds revocation page
 - adds delivery page
 - adds privacy page
 - adds imprint page
 - adds a note on payment site, that terms and revocation are accepted with click on "Pay now"
 - adds terms and revocation popup on payment site; both are taken from terms and revocation page on the frontend


Contact for questions
---------------------
copado MEDIA UG - Unterdorfstr. 29 - 77948 Friesenheim - Germany - Phone: +49 7821 32725 20 - info@copado.de - http:www.copado.de
        """,
    'author': 'copado MEDIA UG, Mathias Neef',
    'website': 'http://www.copado.de',
    'depends': ['website_sale'],
    'data': [
        'views/views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
}