# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import io
import zipfile
from odoo import _, exceptions, fields, models
from ..datev import DatevAccountWriter, DatevPartnerWriter, DatevTransactionWriter


class L10nDeDatevExport(models.Model):
    _name = "l10n_de_datev.export"
    _rec_name = "fiscalyear_id"
    _description = "DATEV export"
    _order = "fiscalyear_id desc, create_date desc"

    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")], default="draft", copy=False
    )
    fiscalyear_id = fields.Many2one(
        "date.range",
        states={"draft": [("required", True), ("readonly", False)]},
        readonly=True,
    )
    fiscalyear_start = fields.Date(related=["fiscalyear_id", "date_start"])
    fiscalyear_end = fields.Date(related=["fiscalyear_id", "date_end"])
    period_ids = fields.Many2many(
        "date.range",
        states={"draft": [("required", True), ("readonly", False)]},
        readonly=True,
    )
    date_generated = fields.Datetime("Generated at", readonly=True, copy=False)
    file_data = fields.Binary("Data", readonly=True, copy=False)
    file_name = fields.Char("Filename", readonly=True, copy=False)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(),
    )

    def action_generate(self):
        for this in self:
            if not all(
                (
                    this.company_id.datev_consultant_id,
                    this.company_id.datev_client_id,
                    this.company_id.datev_account_code_length,
                )
            ):
                raise exceptions.ValidationError(
                    _("Please fill in the DATEV tab of your company")
                )

            zip_buffer = io.BytesIO()
            zip_file = zipfile.ZipFile(zip_buffer, mode="w")

            account_code_length = this.company_id.datev_account_code_length
            user_initials = "".join(
                token[:1].upper() for token in self.env.user.name.split()
            )[:2]

            for date_range in this.period_ids:
                moves = self.env["account.move"].search(
                    [
                        ("state", "=", "posted"),
                        ("date", ">=", date_range.date_start),
                        ("date", "<=", date_range.date_end),
                        ("company_id", "=", this.company_id.id),
                    ],
                    order="date desc",
                )
                writer = DatevTransactionWriter(
                    this.company_id.datev_consultant_id,
                    this.company_id.datev_client_id,
                    this.fiscalyear_id.date_start.strftime("%Y%m%d"),
                    account_code_length,
                    date_range.date_start.strftime("%Y%m%d"),
                    date_range.date_end.strftime("%Y%m%d"),
                    user_initials,
                    self.company_id.currency_id.name,
                )
                writer.writeheader()
                for move in moves:
                    writer.writerows(this._get_data_transaction(move))

                filename = (
                    "EXTF_Buchungsstapel_%s.csv"
                    % date_range.date_start.strftime("%Y%m%d")
                )
                zip_file.writestr(filename, writer.buffer.getvalue())

            partners = self.env["res.partner"].search(
                [
                    "|",
                    ("supplier", "=", True),
                    ("customer", "=", True),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", this.company_id.id),
                ]
            )
            writer = DatevPartnerWriter(
                self.company_id.datev_consultant_id,
                self.company_id.datev_client_id,
                this.fiscalyear_id.date_start.strftime("%Y%m%d"),
                account_code_length,
                None,
                None,
                user_initials,
                self.company_id.currency_id.name,
            )
            writer.writeheader()
            for partner in partners:
                writer.writerows(this._get_data_partner(partner))
            zip_file.writestr("EXTF_DebKred_Stamm.csv", writer.buffer.getvalue())

            accounts = self.env["account.account"].search(
                [
                    ("company_id", "=", this.company_id.id),
                ]
            )
            writer = DatevAccountWriter(
                self.company_id.datev_consultant_id,
                self.company_id.datev_client_id,
                this.fiscalyear_id.date_start.strftime("%Y%m%d"),
                account_code_length + 1,
                None,
                None,
                user_initials,
                self.company_id.currency_id.name,
            )
            writer.writeheader()
            for account in accounts:
                writer.writerows(this._get_data_account(account))
            zip_file.writestr("EXTF_Kontenbeschriftungen.csv", writer.buffer.getvalue())

            zip_file.close()
            this.write(
                {
                    "file_name": "%s.zip" % self.display_name,
                    "file_data": base64.b64encode(zip_buffer.getvalue()),
                    "state": "done",
                    "date_generated": fields.Datetime.now(),
                }
            )

    def _get_data_transaction(self, move):
        # split move into single transactions from one account to another
        move_line2amount = {
            move_line: move_line.credit or move_line.debit
            for move_line in move.line_ids
        }
        currency = move.currency_id or move.company_id.currency_id
        code_length = move.company_id.datev_account_code_length
        while move_line2amount:
            move_line = min(move_line2amount, key=move_line2amount.get)
            amount = move_line2amount.pop(move_line)
            move_line2 = move_line
            for move_line2, amount2 in move_line2amount.items():
                if (
                    move_line.debit
                    and not move_line2.debit
                    or move_line.credit
                    and not move_line2.credit
                ):
                    move_line2amount[move_line2] = currency.round(
                        move_line2amount[move_line2] - amount
                    )
                    if currency.is_zero(move_line2amount[move_line2]):
                        move_line2amount.pop(move_line2)
                    break
            if move_line.account_id.internal_type not in (
                "receivable",
                "payable",
            ) and move_line2.account_id.internal_type in ("receivable", "payable"):
                move_line, move_line2 = move_line2, move_line
            data = {
                "Umsatz (ohne Soll/Haben-Kz)": ("%.2f" % abs(amount)).replace(".", ","),
                "Soll/Haben-Kennzeichen": move_line.debit and "S" or "H",
                "Konto": move_line.account_id.code[-code_length:],
                "Gegenkonto (ohne BU-Schlüssel)": move_line2.account_id.code[
                    -code_length:
                ],
                "Buchungstext": move_line.name,
                "Belegdatum": move.date.strftime("%d%m"),
                "Belegfeld 1": move.name,
                "Belegfeld 2": move_line2.name,
                "KOST1 - Kostenstelle": move_line.analytic_account_id.code
                or move_line.analytic_account_id.name
                or move_line2.analytic_account_id.code
                or move_line2.analytic_account_id.name,
                "KOST-Datum": move.date.strftime("%d%m%Y"),
            }
            if move_line.amount_currency:
                factor = abs(amount / (move_line.debit or move_line.credit))
                data.update(
                    {
                        "Umsatz (ohne Soll/Haben-Kz)": (
                            "%.2f" % abs(move_line.amount_currency * factor)
                        ).replace(".", ","),
                        "WKZ Umsatz": move_line.currency_id.name,
                        "Kurs": (
                            "%.6f"
                            % (
                                1
                                / currency._get_conversion_rate(
                                    move_line.currency_id,
                                    currency,
                                    move.company_id,
                                    move.date,
                                )
                            )
                        ).replace(".", ","),
                        "Basis-Umsatz": ("%.2f" % abs(amount)).replace(".", ","),
                        "WKZ Basis-Umsatz": currency.name,
                    }
                )
            yield data

    def _get_data_partner(self, partner):
        yield {
            "Konto": partner.id,
            "Name (Adressattyp Unternehmen)": partner.name,
            "Name (Adressattyp natürl. Person)": partner.name,
            "Adressattyp": partner.is_company and "2" or "1",
            "EU-Land": partner.country_id.code,
            "EU-UStID": partner.vat,
            "Kurzbezeichnung": partner.ref,
            "Adressart": "STR",
            "Straße": partner.street,
            "Postleitzahl": partner.zip,
            "Ort": partner.city,
            "Land": partner.country_id.code,
            "Telefon": partner.phone,
            "E-Mail": partner.email,
            "Internet": partner.website,
            "IBAN-Nr. 1": partner.bank_ids[:1].acc_number,
            "IBAN-Nr. 2": partner.bank_ids[1:2].acc_number,
            "IBAN-Nr. 3": partner.bank_ids[2:3].acc_number,
            "IBAN-Nr. 4": partner.bank_ids[3:4].acc_number,
            "IBAN-Nr. 5": partner.bank_ids[4:5].acc_number,
            "Kunden-/Lief.-Nr.": partner.ref,
            "Steuernummer": partner.vat,
            "Sprache": "1"
            if (not partner.lang or partner.lang[:2] == "de")
            else "4"
            if partner.lang[:2] == "fr"
            else "10"
            if partner.lang[:2] == "es"
            else "19"
            if partner.lang[:2] == "it"
            else "5",
        }

    def _get_data_account(self, account):
        yield {
            "Konto": account.code[-account.company_id.datev_account_code_length :],
            "Kontobeschriftung": account.name,
            "SprachId": self.env.user.lang.replace("_", "-"),
            "Kontenbeschriftung lang": account.name,
        }
