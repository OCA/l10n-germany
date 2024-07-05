# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import io
import string
import zipfile

from odoo import _, api, exceptions, fields, models
from odoo.osv.expression import TRUE_LEAF

from ..datev import DatevAccountWriter, DatevPartnerWriter, DatevTransactionWriter


class DatevExportDtvfExport(models.Model):
    _name = "datev_export_dtvf.export"
    _description = "DATEV export"
    _order = "fiscalyear_id desc, create_date desc"

    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")], default="draft", copy=False
    )
    fiscalyear_id = fields.Many2one(
        "date.range",
        string="Fiscal year",
        states={"draft": [("required", True), ("readonly", False)]},
        readonly=True,
    )
    name = fields.Char(
        states={"draft": [("required", True), ("readonly", False)]},
        readonly=True,
    )
    fiscalyear_start = fields.Date(related="fiscalyear_id.date_start")
    fiscalyear_end = fields.Date(related="fiscalyear_id.date_end")
    period_ids = fields.Many2many(
        "date.range",
        string="Periods",
        states={"draft": [("required", True), ("readonly", False)]},
        readonly=True,
    )
    journal_ids = fields.Many2many(
        "account.journal",
        string="Journals",
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    date_generated = fields.Datetime("Generated at", readonly=True, copy=False)
    file_data = fields.Binary("Data", readonly=True, copy=False)
    file_name = fields.Char("Filename", readonly=True, compute="_compute_file_name")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.onchange("fiscalyear_id")
    def _onchange_fiscalyear_id(self):
        self.name = self.name or self.fiscalyear_id.display_name

    @api.depends("name")
    def _compute_file_name(self):
        for this in self:
            this.file_name = (
                "".join(
                    c if c in string.ascii_letters + string.digits + "-_" else "_"
                    for c in (this.name or "datev_export")
                )
                + ".zip"
            )

    def action_draft(self):
        return self.filtered(lambda x: x.state != "draft").write({"state": "draft"})

    def action_generate(self):
        for this in self:
            if not all(
                (
                    this.company_id.datev_consultant_number,
                    this.company_id.datev_client_number,
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

            partners = self.env["res.partner"].browse([])

            for date_range in this.period_ids:
                moves = self.env["account.move"].search(
                    [
                        ("state", "=", "posted"),
                        ("date", ">=", date_range.date_start),
                        ("date", "<=", date_range.date_end),
                        ("company_id", "=", this.company_id.id),
                        ("journal_id", "in", this.journal_ids.ids)
                        if this.journal_ids
                        else TRUE_LEAF,
                    ],
                    order="date desc",
                )
                partners += moves.mapped("line_ids.partner_id") + moves.mapped(
                    "partner_id"
                )
                writer = DatevTransactionWriter(
                    this.company_id.datev_consultant_number,
                    this.company_id.datev_client_number,
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

            writer = DatevPartnerWriter(
                self.company_id.datev_consultant_number,
                self.company_id.datev_client_number,
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
                self.company_id.datev_consultant_number,
                self.company_id.datev_client_number,
                this.fiscalyear_id.date_start.strftime("%Y%m%d"),
                account_code_length,
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
            if not move_line.display_type and (move_line.debit or move_line.credit)
        }
        currency = move.currency_id or move.company_id.currency_id
        code_length = move.company_id.datev_account_code_length
        while move_line2amount:
            move_line = min(move_line2amount, key=move_line2amount.get)
            amount = move_line2amount.pop(move_line)
            move_line2 = move_line
            for move_line2 in move_line2amount:
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
            if move_line.account_id.datev_export_nonautomatic:
                move_line, move_line2 = move_line2, move_line
            account_number = move_line.account_id.code[-code_length:]
            offset_account_number = move_line2.account_id.code[-code_length:]
            if self.company_id.datev_partner_numbering in ("ee", "sequence"):
                for ml in (move_line, move_line2):
                    number = (
                        account_number if ml == move_line else offset_account_number
                    )
                    number_type = (
                        "customer"
                        if ml.account_id.internal_type == "receivable"
                        else (
                            "supplier"
                            if ml.account_id.internal_type == "payable"
                            else None
                        )
                    )
                    if number_type and ml.partner_id:
                        number = self._get_partner_number(
                            ml.partner_id, number_type, True
                        )
                    if ml == move_line:
                        account_number = number
                    else:
                        offset_account_number = number
            data = {
                "Umsatz (ohne Soll/Haben-Kz)": ("%.2f" % abs(amount)).replace(".", ","),
                "Soll/Haben-Kennzeichen": move_line.debit and "S" or "H",
                "Konto": account_number,
                "Gegenkonto (ohne BU-Schlüssel)": offset_account_number,
                "BU-Schlüssel": "40"
                if move_line.account_id.datev_export_nonautomatic
                or move_line2.account_id.datev_export_nonautomatic
                else "",
                "Buchungstext": move_line.name,
                "Belegdatum": move.date.strftime("%d%m"),
                "Belegfeld 1": move.name
                if "sale_line_ids" not in move_line._fields
                else (
                    move.mapped(
                        "line_ids.full_reconcile_id.reconciled_line_ids.sale_line_ids.order_id"
                    )
                    or move.mapped("line_ids.sale_line_ids.order_id")
                )[:1].name
                or move.name,
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
        data = {
            "Konto": self._get_partner_number(partner, "customer")
            or self._get_partner_number(partner, "supplier")
            or partner.id,
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
        yield data
        if self._get_partner_number(partner, "customer") and self._get_partner_number(
            partner, "supplier"
        ):
            data["Konto"] = self._get_partner_number(partner, "supplier")
            yield data

    def _get_data_account(self, account):
        yield {
            "Konto": account.datev_code
            or account.code[-account.company_id.datev_account_code_length :],
            "Kontobeschriftung": account.name,
            "SprachId": self.env.user.lang.replace("_", "-"),
            "Kontenbeschriftung lang": account.name,
        }

    def _get_partner_number(self, partner, number_type, generate=False):
        if self.company_id.datev_partner_numbering == "sequence":
            field_name = "l10n_de_datev_export_identifier_%s" % number_type
            if not partner[field_name] and generate:
                getattr(
                    partner,
                    "action_l10n_de_datev_export_identifier_%s" % number_type,
                )()
            return partner[field_name]
        elif self.company_id.datev_partner_numbering == "ee":
            account_length = self.env["account.general.ledger"]._get_account_length()
            return partner[
                "l10n_de_datev_identifier%s"
                % ("_customer" if number_type == "customer" else "")
            ] or str(
                (1 if number_type == "customer" else 7) * 10**account_length
                + partner.id
            )
