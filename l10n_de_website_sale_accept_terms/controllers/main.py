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

from openerp import http
from openerp.http import request

class wsat_additions(http.Controller):
    @http.route(['/page/terms', '/page/website.terms'], type='http', auth='public', website=True)
    def wsat_terms(self, **kw):
        return http.request.render('l10n_de_website_sale_accept_terms.terms')
        
    @http.route(['/page/revocation', '/page/website.revocation'], type='http', auth='public', website=True)
    def wsat_revocation(self, **kw):
        return http.request.render('l10n_de_website_sale_accept_terms.revocation')
        
    @http.route(['/page/delivery', '/page/website.delivery'], type='http', auth='public', website=True)
    def wsat_delivery(self, **kw):
        return http.request.render('l10n_de_website_sale_accept_terms.delivery')
        
    @http.route(['/page/privacy', '/page/website.privacy'], type='http', auth='public', website=True)
    def wsat_privacy(self, **kw):
        return http.request.render('l10n_de_website_sale_accept_terms.privacy')

    @http.route(['/page/imprint', '/page/website.imprint'], type='http', auth='public', website=True)
    def wsat_imprint(self, **kw):
        return http.request.render('l10n_de_website_sale_accept_terms.imprint')
        
wsat_additions()


class wsat_popover(http.Controller):
    @http.route('/popover/terms/', auth="public", type='http')
    def wsat_popover_terms(self, **kw):
        imd = request.registry['ir.model.data']
        iuv = request.registry['ir.ui.view']

        view_id = imd.get_object_reference(request.cr, request.uid, 'l10n_de_website_sale_accept_terms', 'terms')
        view = iuv.browse(request.cr, request.uid, [(view_id[1])], context=None)
        
        xml_id = view_id[1]
        view_result = view[0].arch
        
        return http.request.render('l10n_de_website_sale_accept_terms.popover_terms', {'html_view': view_result})
        
    @http.route('/popover/revocation/', auth="public", type='http')
    def wsat_popover_revocation(self, **kw):
        imd = request.registry['ir.model.data']
        iuv = request.registry['ir.ui.view']

        view_id = imd.get_object_reference(request.cr, request.uid, 'l10n_de_website_sale_accept_terms', 'revocation')
        view = iuv.browse(request.cr, request.uid, [(view_id[1])], context=None)
        
        xml_id = view_id[1]
        view_result = view[0].arch
        
        return http.request.render('l10n_de_website_sale_accept_terms.popover_revocation', {'html_view': view_result})
        
wsat_popover()