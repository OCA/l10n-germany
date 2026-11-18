# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from functools import partial

from lxml import etree

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round

from ..tools.elster_xml import add_element
from .elster_config import (
    HERSTELLER_ID_PARAM,
    NOT_NEGATIVE,
    USTVA_NAMESPACE,
    XML_POSITIONS,
)


class L10nDeTaxStatement(models.Model):
    _inherit = "l10n.de.tax.statement"

    def _get_elster_hersteller_id(self):
        hersteller_id = (
            self.env["ir.config_parameter"].sudo().get_param(HERSTELLER_ID_PARAM)
        )
        if not hersteller_id or not re.fullmatch(r"\d{5}", hersteller_id):
            raise UserError(
                self.env._(
                    "Set the five digit ELSTER HerstellerID in the accounting "
                    "settings first."
                )
            )
        return hersteller_id

    def _get_elster_steuernummer(self):
        """Return the tax number in the 13 digit format of ELSTER"""
        steuernummer = self.company_id.get_l10n_de_stnr_national()
        if not steuernummer or not re.fullmatch(r"\d{4}0\d{8}", steuernummer):
            raise UserError(
                self.env._(
                    "Set a valid tax number (St.-Nr.) and the federal state on "
                    "the company %(company)s first.",
                    company=self.company_id.name,
                )
            )
        return steuernummer

    def _get_elster_widnr(self):
        """Return the W-IdNr. of the company without its distinguishing
        suffix (e.g. -00001), the schema only takes DE and the nine digits.
        The W-IdNr. is optional, a company without one is exported without
        it."""
        widnr = (self.company_id.l10n_de_widnr or "").replace(" ", "").split("-")[0]
        if not widnr:
            return False
        if re.fullmatch(r"DE\d{9}", widnr):
            return widnr
        raise UserError(
            self.env._(
                "The W-IdNr. %(widnr)s of the company %(company)s isn't valid: "
                "enter it as issued, e.g. DE123456789-00001, or leave it empty.",
                widnr=self.company_id.l10n_de_widnr,
                company=self.company_id.name,
            )
        )

    def _get_elster_kennzahlen(self):
        """Return the declared amounts by Kennzahl as strings, formatted like
        ELSTER wants them: the bases in full euros, the taxes with cents.
        ELSTER doesn't say how to round the bases, they are rounded half up.

        Kennzahlen without an amount are left out, ELSTER only notes a zero.
        But the base and the tax of a line are declared together if one of
        them has an amount, ELSTER rejects one without the other (e.g. Kz35
        without Kz36)."""
        self.ensure_one()
        amounts = {"83": f"{self.tax_total:.2f}"}
        for line in self.line_ids.filtered(lambda line: not line.display_type):
            line_amounts = {}
            if line.base_code:
                base = float_round(line.base, 0, rounding_method="HALF-UP")
                line_amounts[line.base_code] = str(int(base))
            if line.tax_code:
                line_amounts[line.tax_code] = f"{line.tax:.2f}"
            if any(float(amount) for amount in line_amounts.values()):
                amounts.update(line_amounts)
        for code, amount in amounts.items():
            if code in NOT_NEGATIVE and float(amount) < 0:
                raise UserError(
                    self.env._("Kennzahl %(code)s can't be negative.", code=code)
                )
        # the schema wants the Kennzahlen in its order, see STATEMENT_ROWS
        return dict(sorted(amounts.items(), key=lambda item: XML_POSITIONS[item[0]]))

    def _get_elster_datenlieferant(self):
        """Return the address of the company, ELSTER requires name, street,
        zip and city of the one who delivers the data"""
        partner = self.company_id.partner_id
        values = {
            "Name": (partner.name or "")[:45],
            "Strasse": (partner.street or "")[:30],
            "PLZ": (partner.zip or "")[:12],
            "Ort": (partner.city or "")[:30],
            "Telefon": (partner.phone or "")[:20],
            "Email": (partner.email or "")[:70],
        }
        missing = [
            name for name in ("Name", "Strasse", "PLZ", "Ort") if not values[name]
        ]
        if missing:
            raise UserError(
                self.env._(
                    "Set the address of the company %(company)s first, ELSTER "
                    "requires name, street, zip and city.",
                    company=self.company_id.name,
                )
            )
        return {name: value for name, value in values.items() if value}

    def _get_elster_xml(self):
        """Return the statement as ELSTER XML for the upload in Mein ELSTER:
        the Anmeldungssteuern of the UStVA schema, without the envelope of a
        transmission with ERiC"""
        self.ensure_one()
        hersteller_id = self._get_elster_hersteller_id()
        steuernummer = self._get_elster_steuernummer()
        datenlieferant = self._get_elster_datenlieferant()
        namespace = USTVA_NAMESPACE.format(year=self.year)

        sub = partial(add_element, namespace)

        anmeldungssteuern = etree.Element(
            f"{{{namespace}}}Anmeldungssteuern",
            {"version": str(self.year)},
            nsmap={None: namespace},
        )
        sub(
            anmeldungssteuern,
            "Erstellungsdatum",
            fields.Date.context_today(self).strftime("%Y%m%d"),
        )
        datenlieferant_element = sub(anmeldungssteuern, "DatenLieferant")
        for name, value in datenlieferant.items():
            sub(datenlieferant_element, name, value)
        anmeldung = sub(
            sub(anmeldungssteuern, "Steuerfall"), "Umsatzsteuervoranmeldung"
        )
        sub(anmeldung, "Jahr", str(self.year))
        sub(anmeldung, "Zeitraum", self.period)
        sub(anmeldung, "Steuernummer", steuernummer)
        widnr = self.year >= 2025 and self._get_elster_widnr()
        if widnr:
            sub(anmeldung, "WIdNr", widnr)
        # Kz09 and Kz10 aren't amounts of the form, the schema puts them first
        sub(anmeldung, "Kz09", hersteller_id)
        if self.is_corrected:
            sub(anmeldung, "Kz10", "1")
        for code, amount in self._get_elster_kennzahlen().items():
            sub(anmeldung, f"Kz{code}", amount)
        return etree.tostring(
            anmeldungssteuern, xml_declaration=True, encoding="UTF-8", pretty_print=True
        )

    def _get_elster_product_version(self):
        module = (
            self.env["ir.module.module"]
            .sudo()
            .search([("name", "=", "l10n_de_tax_statement")], limit=1)
        )
        return module.latest_version or "1"

    def _create_elster_xml_attachment(self):
        """Attach the statement as ELSTER XML for the upload in Mein ELSTER"""
        self.ensure_one()
        return self.env["ir.attachment"].create(
            {
                "name": f"UStVA_{self.year}_{self.period}.xml",
                "raw": self._get_elster_xml(),
                "mimetype": "application/xml",
                "res_model": self._name,
                "res_id": self.id,
            }
        )
