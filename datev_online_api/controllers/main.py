# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

from werkzeug.exceptions import BadRequest, Forbidden

from odoo import http
from odoo.http import request
from odoo.tools import consteq

_logger = logging.getLogger(__name__)


class DatevApiAuth(http.Controller):
    @http.route("/datev/authentication", type="http", auth="public")
    def datev_oauth_callback(self, **kw):
        """Handle the redirect of the user with the authorization data"""

        code = kw.get("code")
        state = json.loads(kw.get("state", "{}"))
        csrf = state.get("csrf")
        company_id = state.get("id")

        company = request.env["res.company"].sudo().search([("id", "=", company_id)])
        if not company:
            raise BadRequest()

        if not csrf or not consteq(csrf, company._datev_hmac_csrf()):
            _logger.error("DATEV API: Wrong CSRF token during datev authentication")
            raise Forbidden()

        action = company.env.ref("account.action_account_config", False)
        url_return = f"/odoo/action-{action.id}" if action else "/odoo"
        if code:
            base_url = (
                request.httprequest.url_root.strip("/")
                or request.env.user.get_base_url()
            )

            company._datev_get_token(
                code, redirect_uri=f"{base_url}/datev/authentication"
            )
            return request.redirect(url_return)

        if error := kw.get("error"):
            _logger.error(f"DATEV API: oauth error {error!r}")
            return request.redirect(f"{url_return}?error={error}")

        return request.redirect(f"{url_return}?error=Unknown error")
