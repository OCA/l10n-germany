# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import os
import unittest
from contextlib import contextmanager
from datetime import date
from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo.tools import config

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.l10n_de_tax_statement.models.elster_config import (
    HERSTELLER_ID_PARAM,
)

from ..models.l10n_de_tax_statement import LIBRARY_OPTION
from ..tools.eric import ERIC_GLOBAL_PRUEF_FEHLER, ERIC_OK, ERIC_SENDE, Eric, EricResult

RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<EricBearbeiteVorgang
    xmlns="http://www.elster.de/EricXML/1.2/EricBearbeiteVorgang">
  <Erfolg/>
</EricBearbeiteVorgang>"""
SERVER_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<Elster xmlns="http://www.elster.de/elsterxml/schema/v11">
  <TransferHeader version="11">
    <TransferTicket>%s</TransferTicket>
    <RC><Rueckgabe><Code>0</Code>
      <Text>Daten wurden erfolgreich angenommen.</Text></Rueckgabe></RC>
  </TransferHeader>
</Elster>"""
HINT_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<EricBearbeiteVorgang
    xmlns="http://www.elster.de/EricXML/1.2/EricBearbeiteVorgang">
  <Hinweis>
    <Nutzdatenticket>1</Nutzdatenticket>
    <Text>Bitte die Kennzahl 83 prüfen.</Text>
  </Hinweis>
</EricBearbeiteVorgang>"""
ERROR_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<EricBearbeiteVorgang
    xmlns="http://www.elster.de/EricXML/1.2/EricBearbeiteVorgang">
  <FehlerRegelpruefung>
    <Nutzdatenticket>1</Nutzdatenticket>
    <Text>Die Steuernummer ist ungültig.</Text>
  </FehlerRegelpruefung>
</EricBearbeiteVorgang>"""

# Sends to the test interface of ELSTER when set, see EricTestSendCase
TEST_SEND = "L10N_DE_ERIC_TEST_SEND"
# The test certificate of ERiC, next to the library in Beispiel by default
TEST_CERTIFICATE = "L10N_DE_ERIC_TEST_CERTIFICATE"
TEST_CERTIFICATE_DEFAULT = "../Beispiel/ericdemo-python/test-softidnr-pse.pfx"
TEST_PIN = "L10N_DE_ERIC_TEST_PIN"
TEST_PIN_DEFAULT = "123456"
# The HerstellerID of the developer, ELSTER blocks the one of its examples
TEST_HERSTELLER_ID = "L10N_DE_ERIC_TEST_HERSTELLER_ID"


def _get_test_send_settings():
    """Return the library, the test certificate, its PIN and the HerstellerID
    for the test interface of ELSTER, or the reason to skip"""
    if not os.environ.get(TEST_SEND):
        return None, f"set {TEST_SEND} to send to the test interface of ELSTER"
    library = os.environ.get(LIBRARY_OPTION.upper())
    if not library:
        return None, f"set {LIBRARY_OPTION.upper()} to the path of libericapi.so"
    hersteller_id = os.environ.get(TEST_HERSTELLER_ID)
    if not hersteller_id:
        return None, f"set {TEST_HERSTELLER_ID} to your HerstellerID"
    certificate = os.environ.get(TEST_CERTIFICATE) or os.path.join(
        os.path.dirname(library), TEST_CERTIFICATE_DEFAULT
    )
    if not os.path.isfile(certificate):
        return None, f"set {TEST_CERTIFICATE} to the test certificate of ERiC"
    with open(certificate, "rb") as file:
        certificate = file.read()
    pin = os.environ.get(TEST_PIN, TEST_PIN_DEFAULT)
    return (library, certificate, pin, hersteller_id), None


TEST_SEND_SETTINGS, TEST_SEND_SKIP_REASON = _get_test_send_settings()


class EricFakeCase(BaseCommon):
    """Replace ERiC by a fake which records its calls in ``self.calls``. The
    subclasses set ``cls.statement``."""

    # the transfer ticket of a sent Datenartversion, "ab1234" by default
    fake_tickets = {}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calls = []

    @contextmanager
    def _fake_eric(self, fail=False, server_response=None, response=RESPONSE):
        """``fail``: True or a function of the Datenartversion and whether it
        is sent, the failing calls return a failed Plausibilitätsprüfung.
        ``server_response`` replaces the answer of ELSTER to a sending,
        ``response`` the answer of ERiC."""
        test = self

        class FakeEric:
            def process(self, xml, datenart_version, flags, **kwargs):
                test.calls.append((xml, datenart_version, flags, kwargs))
                sending = bool(flags & ERIC_SENDE)
                if fail is True or (fail and fail(datenart_version, sending)):
                    return EricResult(
                        ERIC_GLOBAL_PRUEF_FEHLER,
                        "Fehler bei der Plausibilitätsprüfung",
                        ERROR_RESPONSE,
                        "",
                        {},
                    )
                answer = ""
                if sending:
                    ticket = test.fake_tickets.get(datenart_version, "ab1234")
                    answer = (
                        SERVER_RESPONSE % ticket
                        if server_response is None
                        else server_response
                    )
                return EricResult(ERIC_OK, "", response, answer, {"1": b"%PDF-1.4"})

        @contextmanager
        def session(eric):
            yield FakeEric()

        self.calls.clear()
        with (
            patch.dict(config.options, {LIBRARY_OPTION: "/opt/libericapi.so"}),
            patch.object(Eric, "session", session),
        ):
            yield

    def _get_sent(self):
        """Return the Datenartversionen sent, in their order"""
        return [call[1] for call in self.calls if call[2] & ERIC_SENDE]

    def _send(self, action=None, **vals):
        """Send with the dialog of ``action``, the dialog of the statement by
        default; it removes the certificate and the PIN afterwards"""
        context = (
            action["context"] if action else {"default_statement_id": self.statement.id}
        )
        wizard = (
            self.env["l10n.de.tax.statement.eric.send"]
            .with_context(**context)
            .create(
                {
                    "certificate": base64.b64encode(b"pfx"),
                    "pin": "1234",
                    "privacy_notice_read": True,
                    **vals,
                }
            )
        )
        try:
            wizard.action_send()
        finally:
            wizard.invalidate_recordset()
            self.assertFalse(wizard.certificate)
            self.assertFalse(wizard.pin)

    def _store_credentials(self, certificate=b"stored", pin="4321"):
        self.statement.company_id.write(
            {
                "l10n_de_eric_store_certificate": True,
                "l10n_de_eric_certificate": base64.b64encode(certificate),
                "l10n_de_eric_pin": pin,
            }
        )
        self.env.user._l10n_de_eric_confirm_privacy_notice()


@unittest.skipUnless(TEST_SEND_SETTINGS, TEST_SEND_SKIP_REASON)
class EricTestSendCase(BaseCommon):
    """Send to the test interface of ELSTER with the real ERiC: only with
    L10N_DE_ERIC_TEST_SEND set, and L10N_DE_ERIC_LIBRARY and
    L10N_DE_ERIC_TEST_HERSTELLER_ID. The test certificate of ERiC only sends
    test cases, which ELSTER deletes right after their receipt."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _library, certificate, pin, hersteller_id = TEST_SEND_SETTINGS
        cls.certificate, cls.pin = certificate, pin
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test company",
                "country_id": cls.env.ref("base.de").id,
                "state_id": cls.env.ref("base.state_de_bw").id,
                "currency_id": cls.env.ref("base.EUR").id,
                "street": "Testgasse 13",
                "zip": "08151",
                "city": "Musterstadt",
                "phone": "0815 99999",
                "vat": "DE123456788",
                "l10n_de_eric_test": True,
            }
        )
        cls.company.l10n_de_stnr = "93815/08152"
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            HERSTELLER_ID_PARAM, hersteller_id
        )
        cls.env["account.chart.template"].try_loading("de_skr03", cls.company)
        # the last month: a period ERiC supports
        cls.period_date = date.today().replace(day=15) - relativedelta(months=1)

    def _store_credentials(self):
        self.company.write(
            {
                "l10n_de_eric_store_certificate": True,
                "l10n_de_eric_certificate": base64.b64encode(self.certificate),
                "l10n_de_eric_pin": self.pin,
            }
        )
        self.env.user._l10n_de_eric_confirm_privacy_notice()

    def _create_statement(self):
        return self.env["l10n.de.tax.statement"].create(
            {
                "company_id": self.company.id,
                "year": self.period_date.year,
                "period": f"{self.period_date.month:02d}",
            }
        )

    def _get_transmission(self, statement, name):
        """Return the message of the test transmission ``name``"""
        return statement.message_ids.filtered(
            lambda message: f"ELSTER received {name} as a test" in message.body
        )

    def _assert_accepted(self, statement, name):
        message = self._get_transmission(statement, name)
        self.assertEqual(len(message), 1, f"no transmission of {name}")
        self.assertIn("Transfer ticket:", message.body)
        self.assertEqual(message.attachment_ids.name, f"{name}_Protokoll.pdf")
        self.assertTrue(message.attachment_ids.raw.startswith(b"%PDF"))
