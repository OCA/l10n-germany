# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib
import json
import logging
import secrets
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from werkzeug.urls import url_join

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.misc import hmac

_logger = logging.getLogger(__name__)


DATEV_API = {
    "login": {
        "live": "https://login.datev.de/openid/.well-known/openid-configuration",
        "test": "https://login.datev.de/openidsandbox/.well-known/openid-configuration",
    },
    "accounting": {
        "live": "https://accounting-clients.api.datev.de/platform/v2",
        "test": "https://accounting-clients.api.datev.de/platform-sandbox/v2",
    },
}


def is_expired(time):
    return not time or time < datetime.now()


class ResCompany(models.Model):
    _inherit = "res.company"

    datev_api = fields.Selection(
        [("disabled", "Disabled"), ("test", "Testing"), ("live", "Live")],
        required=True,
        default="disabled",
    )
    datev_api_long_term = fields.Boolean(default=True)
    datev_api_client_id = fields.Char(copy=False)
    datev_api_client_secret = fields.Char(copy=False)
    datev_api_code_verifier = fields.Char(copy=False, groups="base.group_system")
    datev_api_refresh_token = fields.Char(groups="base.group_system")
    datev_api_refresh_token_expire = fields.Datetime(groups="base.group_system")
    datev_api_token = fields.Char(groups="base.group_system")
    datev_api_token_expire = fields.Datetime(groups="base.group_system")
    datev_api_service_ids = fields.Many2many("datev.api.service", readonly=True)
    datev_api_available = fields.Boolean(compute="_compute_datev_available")

    @api.depends("datev_api_refresh_token_expire", "datev_api")
    def _compute_datev_available(self):
        for rec in self:
            rec.datev_api_available = rec.datev_api in (
                "test",
                "live",
            ) and not is_expired(rec.datev_api_refresh_token_expire)

    def action_datev_api_authorization(self):
        """Redirect the user to DATEV for the OAuth authorization"""

        self.ensure_one()
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(
                self.env._("Only the adminstrator can link the DATEV API server")
            )

        if not self.datev_api_client_id or not self.datev_api_client_secret:
            raise UserError(self.env._("Please configure your credentials first"))

        if not self.datev_consultant_number or not self.datev_client_number:
            raise UserError(
                self.env._("Please configure your consultant and client number")
            )

        url, params = self._datev_get_auth_url()
        return {
            "type": "ir.actions.act_url",
            "url": f"{url}?{urlencode(params)}",
            "target": "self",
        }

    def action_datev_api_revoke(self):
        """Revoke the API tokens"""

        self.ensure_one()
        self._datev_revoke_token()

    def _datev_api_scope(self):
        """Overwrite to extend the scope of the API"""

        scopes = {"openid", "profile", "datev:accounting:clients"}
        if (
            self.datev_consultant_number
            and self.datev_client_number
            and self.datev_api_long_term
        ):
            scopes |= {
                "offline_access",
                f"datev:iam:client:{self.datev_consultant_number}-{self.datev_client_number}",
            }
        return scopes

    def _datev_api_url(self, endpoint):
        return DATEV_API.get(endpoint, {}).get(self.datev_api)

    def _datev_oidc_configuration(self):
        """Fetch the OIDC configuration of datev for the OAuth configurations"""

        self.ensure_one()

        url = self._datev_api_url("login")
        if not url:
            raise UserError(self.env._("Please select DATEV API"))

        site = requests.get(url, timeout=1)
        if site.status_code != 200:
            raise UserError(self.env._("There was a error in the DATEV API"))

        return site.json()

    def _datev_generate_pkce(self):
        """Generate a challenge and verifier for the OAuth authorization flow"""

        def urlsafe_code(code):
            return urlsafe_b64encode(code).decode("utf-8").rstrip("=")

        code_verifier = urlsafe_code(secrets.token_bytes(32))
        code_challenge = urlsafe_code(hashlib.sha256(code_verifier.encode()).digest())
        return code_verifier, code_challenge

    def _datev_get_auth_url(self):
        """Return the authorization url and params to redirect the user"""

        self.ensure_one()
        config = self._datev_oidc_configuration()

        if "S256" not in config.get("code_challenge_methods_supported", []):
            raise UserError(
                self.env._("The code challenge method is currently not supported")
            )

        state = {
            "id": self.id,
            "csrf": self._datev_hmac_csrf(),
        }

        self.datev_api_code_verifier, code_challenge = self._datev_generate_pkce()

        params = {
            "response_type": "code",
            "client_id": self.datev_api_client_id,
            "state": json.dumps(state),
            "nonce": secrets.token_urlsafe(20),
            "scope": " ".join(self._datev_api_scope()),
            "redirect_uri": f"{self.get_base_url()}/datev/authentication",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        return config["authorization_endpoint"], params

    def _datev_hmac_csrf(self):
        """Build an HMAC as CSRF"""

        return hmac(
            env=self.env(su=True),
            scope="datev_api_oauth",
            message=(self._name, self.id),
        )

    def _datev_get_token(self, code, redirect_uri):
        """Get a new token as part of the authorization process"""

        self.ensure_one()

        data = self._datev_fetch_token(
            "authorization_code",
            code=code,
            code_verifier=self.datev_api_code_verifier,
            redirect_uri=redirect_uri,
        )

        if not data:
            _logger.error("Authorization failed")
            return

        self._datev_set_tokens(data)
        self.datev_api_code_verifier = False

        self._datev_client_information()

    def _datev_refresh_token(self):
        """Refresh the tokens"""

        self.ensure_one()

        data = self._datev_fetch_token(
            "refresh_token",
            refresh_token=self.datev_api_refresh_token,
            scope="offline_access",
        )
        if not data:
            _logger.error("Refreshing the token failed")
            return False

        self._datev_set_tokens(data)
        return True

    def _datev_set_tokens(self, data):
        """Store the refreshed tokens on the company"""

        def get_expire_time(seconds):
            return datetime.now() + timedelta(seconds=seconds)

        self.ensure_one()
        self.write(
            {
                "datev_api_refresh_token": data["refresh_token"],
                "datev_api_refresh_token_expire": get_expire_time(
                    data["refresh_token_expires_in"]
                ),
                "datev_api_token": data["access_token"],
                "datev_api_token_expire": get_expire_time(data["expires_in"]),
            }
        )

        # We have to store the tokens otherwise if this transactions aborts
        # the refresh token is invalid and reusing it will invalidate the entire
        # authorization
        # pylint: disable=invalid-commit
        self.env.cr.commit()

    def _datev_fetch_token(self, grant_type, scope=None, **values):
        """Generic function to fetch/refresh the tokens via the API"""

        self.ensure_one()

        config = self._datev_oidc_configuration()

        response = requests.post(
            config["token_endpoint"],
            headers={"Content-type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": grant_type,
                "scope": scope or " ".join(self._datev_api_scope()),
                "redirect_uri": url_join(self.get_base_url(), "/datev/authentication"),
                **values,
            },
            auth=(self.datev_api_client_id, self.datev_api_client_secret),
            timeout=5,
        )

        if response.status_code != 200:
            _logger.error(f"Error while fetching token: {response.text}")
            return None

        return response.json()

    def _datev_revoke_token(self):
        """Revoke the token"""

        self.ensure_one()

        config = self._datev_oidc_configuration()

        for token_field in ("token", "refresh_token"):
            token = getattr(self, f"datev_api_{token_field}")
            if not token:
                continue

            response = requests.post(
                config["revocation_endpoint"],
                data={"token": token},
                auth=(self.datev_api_client_id, self.datev_api_client_secret),
                timeout=5,
            )

            if response.status_code == 200:
                self.write(
                    {
                        f"datev_api_{token_field}": None,
                        f"datev_api_{token_field}_expire": None,
                    }
                )

    def _datev_request_get(self, url):
        """Do a GET request against the url with the client ID and access token"""

        self._datev_ensure_api_token()

        response = requests.get(
            url,
            headers={
                "Accept": "application/json;charset=utf-8",
                "Authorization": f"Bearer {self.datev_api_token}",
                "X-DATEV-Client-Id": self.datev_api_client_id,
            },
            timeout=5,
        )

        if response.status_code != 200:
            _logger.error(f"Error on request: {response.text}")
            return None

        return response.json()

    def _datev_ensure_api_token(self):
        if is_expired(self.datev_api_refresh_token_expire):
            raise UserError(self.env._("The process requires a re-authentication"))

        if is_expired(self.datev_api_token_expire) and not self._datev_refresh_token():
            raise UserError(
                self.env._(
                    "Unable to refresh token. You might need to re-authenticate."
                )
            )

    def _datev_client_information(self):
        """Fetch the client informations from the accounting API"""

        self.ensure_one()
        url = self._datev_api_url("accounting")
        client_id = f"{self.datev_consultant_number}-{self.datev_client_number}"

        data = self._datev_request_get(f"{url}/clients/{client_id}")
        if not data:
            return

        api_scope = set(self._datev_api_scope())

        # Generate all possible services and link the supported services
        services = self.datev_api_service_ids.browse()
        for service_data in data.get("services", []):
            name, scopes = map(service_data.get, ("name", "scopes"))
            scopes = scopes or []
            if not name:
                continue

            service = services.find_service_or_create(name, " ".join(scopes))

            if api_scope.issuperset(scopes):
                services |= service

        self.datev_api_service_ids = services

    def cron_datev_tasks(self):
        """Run regular tasks"""

        for company in self.search([]):
            company._datev_ensure_api_token()
            if company.datev_api_available:
                company._cron_datev_tasks()

    def _cron_datev_tasks(self):
        """Overwrite to add additional synchronisation tasks"""
        ...
