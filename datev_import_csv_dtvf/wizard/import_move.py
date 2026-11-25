# Copyright 2012-2019 Akretion France (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import csv
import logging
from datetime import date as datelib
from datetime import datetime

import chardet

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)

GENERIC_CSV_DEFAULT_DATE = "%d/%m/%Y"


class AccountMoveImport(models.TransientModel):
    _name = "account.move.import"
    _description = "Import account move from CSV file"

    file_to_import = fields.Binary(
        string="File to Import",
        required=True,
        help="File containing the journal entry(ies) to import.",
    )
    filename = fields.Char()
    post_move = fields.Boolean(
        string="Post Journal Entry",
        help="If True, the journal entry will be posted after the import.",
    )
    force_journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        help="Journal in which the journal entry will be created",
    )
    force_move_ref = fields.Char("Reference")
    force_move_line_name = fields.Char("Force Label")
    force_move_date = fields.Date("Force Date")
    date_format = fields.Char(
        default=GENERIC_CSV_DEFAULT_DATE,
        required=True,
        help='Date format is applicable only on Generic csv file ex "%d%m%Y"',
    )
    apply_account_taxes = fields.Boolean(
        string="Apply Account Default Taxes",
        help="If enabled, taxes configured on accounts (Automatikkonten) will be "
        "applied automatically. The imported amounts are treated as gross "
        "(tax-included) and will be split into net amount + tax lines.",
    )

    def run_import(self):
        self.ensure_one()
        file_bytes = base64.b64decode(self.file_to_import)
        pivot = self.genericcsv2pivot(file_bytes)
        _logger.debug("pivot before update: %s", pivot)
        self.clean_strip_pivot(pivot)
        self.update_pivot(pivot)
        moves = self.create_moves_from_pivot(pivot, post=self.post_move)
        action = {
            "name": self.env._("Imported Journal Entries"),
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "nodestroy": False,
            "target": "current",
        }

        if len(moves) == 1:
            action.update(
                {
                    "view_mode": "form,list",
                    "res_id": moves[0].id,
                }
            )
        else:
            action.update(
                {
                    "view_mode": "list,form",
                    "domain": Domain("id", "in", moves.ids),
                }
            )
        return action

    def clean_strip_pivot(self, pivot):
        for l in pivot:  # noqa: E741
            for key, value in l.items():
                if value:
                    if isinstance(value, str):
                        l[key] = value.strip() or False
                else:
                    l[key] = False

    def update_pivot(self, pivot):
        force_move_date = self.force_move_date
        force_move_ref = self.force_move_ref
        force_move_line_name = self.force_move_line_name
        force_journal_code = (
            self.force_journal_id and self.force_journal_id.code or False
        )
        for l in pivot:  # noqa: E741
            if force_move_date:
                l["date"] = force_move_date
            if force_move_line_name:
                l["name"] = force_move_line_name
            if force_move_ref:
                l["ref"] = force_move_ref
            if force_journal_code:
                l["journal"] = force_journal_code
            if not l["credit"]:
                l["credit"] = 0.0
            if not l["debit"]:
                l["debit"] = 0.0

    def genericcsv2pivot(self, file_bytes):
        # Prisme
        fieldnames = [
            "sales",
            "indicator",
            "wkz_sales",
            "course",
            "basic_sales",
            "wkz_base_sales",
            "account",
            "contra_account",
            "BU_key",
            "date",
            "doc_field_1",
            "doc_field_2",
            "discount",
            "name",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "/",
            "analytic_account_1",
            "analytic_account_2",
        ]
        content = file_bytes.decode(chardet.detect(file_bytes)["encoding"])
        try:
            dialect = csv.Sniffer().sniff(content, delimiters=";,")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(
            content.splitlines(),
            fieldnames=fieldnames,
            delimiter=dialect.delimiter,
            quotechar=dialect.quotechar,
            quoting=csv.QUOTE_MINIMAL,
        )
        res = []
        year_str = ""
        i = 0
        for l in reader:  # noqa: E741
            i += 1
            if i == 1 and l["discount"]:
                year_str = l["discount"][0:4]
            if i >= 3:
                date_str = l["date"][0:2] + "/" + l["date"][-2:] + "/" + year_str
                try:
                    date = datetime.strptime(date_str, self.date_format)
                except Exception as error:
                    raise UserError(
                        (  # pylint: disable=translation-not-lazy
                            self.env._(
                                "time data : '%(date)s' in line %(number)s does not "
                                "match format '%(format)s"
                            )
                        )
                        % {"date": date_str, "number": i, "format": self.date_format}
                    ) from error
                vals = {
                    "journal": self.force_journal_id.id,
                    "account": l["account"],
                    "contra_account": l["contra_account"],
                    "credit": float(l["sales"].replace(",", ".") or 0),
                    "debit": float(l["sales"].replace(",", ".") or 0),
                    "date": date,
                    "name": l["name"],
                    "ref": l.get("indicator", "").upper()
                    if not self.force_move_ref
                    else self.force_move_ref,
                    "indicator": l.get("indicator", "").upper(),
                    "line": i,
                    "analytic_account_1": l["analytic_account_1"],
                    "analytic_account_2": l["analytic_account_2"],
                }
                res.append(vals)
        return res

    def _enrich_pivot_with_taxes(self, pivot, acc_tax_dict):
        """Compute net amounts from gross using Odoo's tax pipeline with round_globally.

        Uses _prepare_base_line_for_taxes_computation + _add_tax_details_in_base_lines
        + _round_base_lines_tax_details so that rounding redistribution across lines
        sharing the same tax is handled by Odoo's standard mechanism.
        """
        AccountTax = self.env["account.tax"]
        company = self.env.company

        # Collect base lines for both account and contra_account sides
        base_line_map = []  # list of (pivot_line, side, taxes, gross)
        for l in pivot:  # noqa: E741
            gross = l["debit"] or l["credit"]
            if not gross:
                continue
            acc_taxes = acc_tax_dict.get(l.get("account_id"))
            if acc_taxes:
                base_line_map.append((l, "account", acc_taxes, gross))
            contra_taxes = acc_tax_dict.get(l.get("contra_account_id"))
            if contra_taxes:
                base_line_map.append((l, "contra", contra_taxes, gross))

        if not base_line_map:
            return

        # Build Odoo base lines with special_mode='total_included'
        base_lines = []
        for _pivot_line, _side, taxes, gross in base_line_map:
            bl = AccountTax._prepare_base_line_for_taxes_computation(
                None,
                tax_ids=taxes,
                price_unit=gross,
                quantity=1.0,
                special_mode="total_included",
                currency_id=company.currency_id,
            )
            base_lines.append(bl)

        # Compute tax details and apply round_globally redistribution
        AccountTax._add_tax_details_in_base_lines(base_lines, company)
        AccountTax._round_base_lines_tax_details(base_lines, company)

        # Write rounded net amounts back to pivot lines.
        # delta_total_excluded contains the round_globally adjustment.
        for (pivot_line, side, taxes, _gross), bl in zip(
            base_line_map, base_lines, strict=False
        ):
            td = bl["tax_details"]
            net = td["total_excluded"] + td.get("delta_total_excluded", 0.0)
            if side == "account":
                pivot_line["tax_ids"] = taxes.ids
                pivot_line["net_amount"] = net
            else:
                pivot_line["contra_tax_ids"] = taxes.ids
                pivot_line["contra_net_amount"] = net

        _logger.debug(
            "Tax enrichment: %d lines enriched via round_globally pipeline",
            len(base_line_map),
        )

    def create_moves_from_pivot(self, pivot, post=False):  # noqa: C901
        _logger.debug("Final pivot: %s", pivot)
        ctx = {} if self.apply_account_taxes else {"skip_invoice_sync": True}
        amo = self.env["account.move"].with_context(**ctx)
        company_id = self.env.company.id
        # Generate SPEED DICTS
        # account
        acc_speed_dict = {
            account["code"].upper(): account["id"]
            for account in self.env["account.account"].search_read(
                Domain.AND(
                    [
                        Domain("company_ids", "any", Domain("id", "=", company_id)),
                        Domain("active", "=", True),
                    ]
                ),
                ["code"],
            )
        }
        # contra_account
        accc_speed_dict = acc_speed_dict.copy()
        # journal
        journal_speed_dict = {
            journal["code"].upper(): journal["id"]
            for journal in self.env["account.journal"].search_read(
                Domain("company_id", "=", company_id), ["code"]
            )
        }
        # analytic account
        analytic_speed_dict = {
            (
                analytic_account["code"] or analytic_account["name"]
            ).upper(): analytic_account["id"]
            for analytic_account in self.env["account.analytic.account"].search_read(
                Domain("company_id", "=", company_id), ["code", "name"]
            )
        }
        # account default taxes (for Automatikkonten)
        acc_tax_dict = {}
        if self.apply_account_taxes:
            for account in self.env["account.account"].search(
                Domain.AND(
                    [
                        Domain("company_ids", "any", Domain("id", "=", company_id)),
                        Domain("active", "=", True),
                        Domain("tax_ids", "!=", False),
                    ]
                )
            ):
                acc_tax_dict[account.id] = account.tax_ids
            _logger.debug("Loaded %d accounts with default taxes", len(acc_tax_dict))
        key2label = {
            "account": self.env._("account codes"),
            "contra_account": self.env._("contra account codes"),
            "journal": self.env._("journal codes"),
            "analytic_account_1": self.env._("analytic account codes"),
            "analytic_account_2": self.env._("analytic account codes"),
        }
        errors = {"other": []}
        for key in key2label.keys():
            errors[key] = {}

        def match_account(line, speed_dict, id_field, code_field):
            line[id_field] = speed_dict.get(line[code_field].upper())
            if not line.get(id_field):
                # Match when import = 61100000 and Odoo has 611000
                acc_code_tmp = line[code_field].upper()
                while acc_code_tmp and acc_code_tmp[-1] == "0":
                    acc_code_tmp = acc_code_tmp[:-1]
                    if acc_code_tmp and acc_code_tmp in speed_dict:
                        line[id_field] = speed_dict[acc_code_tmp]
                        break
            if not line.get(id_field):
                # Match when import = 611000 and Odoo has 611000XX
                for code, account_id in speed_dict.items():
                    if code.startswith(line[code_field]):
                        _logger.warning(
                            f"Approximate match: import account {line[code_field]} "
                            "has been matched "
                            f"with Odoo account {code}"
                        )
                        line[id_field] = account_id
                        break
            if not line.get(id_field):
                errors[code_field].setdefault(line[code_field], []).append(line["line"])

        # MATCHES + CHECKS
        for l in pivot:  # noqa: E741
            assert l.get("line") and isinstance(l.get("line"), int), (
                "missing line number"
            )
            # 1. account
            match_account(l, acc_speed_dict, "account_id", "account")
            # 2. contra_account
            match_account(l, accc_speed_dict, "contra_account_id", "contra_account")
            # 3. journal
            if (l["journal"] or "").upper() in journal_speed_dict:
                l["journal_id"] = journal_speed_dict[(l["journal"] or "").upper()]
            else:
                errors["journal"].setdefault(l["journal"], []).append(l["line"])
            # 4. name
            if not l.get("name"):
                errors["other"].append(
                    self.env._("Line %d: missing label.") % l["line"]  # pylint: disable=translation-not-lazy
                )
            # 5. date
            if not l.get("date"):
                errors["other"].append(self.env._("Line %d: missing date.") % l["line"])  # pylint: disable=translation-not-lazy
            else:
                if not isinstance(l.get("date"), datelib):
                    try:
                        l["date"] = datetime.strptime(l["date"], "%Y-%m-%d")
                    except Exception:
                        errors["other"].append(
                            self.env._("Line %(line)d: bad date format %(date)s") % l  # pylint: disable=translation-not-lazy
                        )
            # 6. credit
            if not isinstance(l.get("credit"), float):
                errors["other"].append(
                    self.env._("Line %(line)d: bad value for credit (%(credit)s).") % l  # pylint: disable=translation-not-lazy
                )
            # 7. debit
            if not isinstance(l.get("debit"), float):
                errors["other"].append(
                    self.env._("Line %(line)d: bad value for debit (%(debit)s).") % l  # pylint: disable=translation-not-lazy
                )
            if l["analytic_account_1"]:
                match_account(
                    l,
                    analytic_speed_dict,
                    "analytic_account_1_id",
                    "analytic_account_1",
                )
            if l["analytic_account_2"]:
                match_account(
                    l,
                    analytic_speed_dict,
                    "analytic_account_2_id",
                    "analytic_account_2",
                )
            # test that they don't have both a value
        # ENRICH WITH TAX DATA
        if self.apply_account_taxes:
            self._enrich_pivot_with_taxes(pivot, acc_tax_dict)
        # LIST OF ERRORS
        msg = ""
        for key, label in key2label.items():
            if errors[key]:
                msg += self.env._(  # pylint: disable=translation-not-lazy
                    "List of %(label)s that don't exist in Odoo:\n%(codes)s\n\n"
                ) % {
                    "label": label,
                    "codes": "\n".join(
                        [
                            "- {} : line(s) {}".format(
                                code, ", ".join([str(i) for i in lines])
                            )
                            for (code, lines) in errors[key].items()
                        ]
                    ),
                }
        if errors["other"]:
            msg += self.env._("List of misc errors:\n%s") % (  # pylint: disable=translation-not-lazy
                "\n".join([f"- {e}" for e in errors["other"]])
            )
        if msg:
            raise UserError(msg)
        # EXTRACT MOVES
        moves = []
        cur_balance = 0.0
        cur_date = False
        prec = self.env.company.currency_id.rounding
        seq = self.env["ir.sequence"].next_by_code("account.move.import")
        cur_move = {}
        for l in pivot:  # noqa: E741
            indicator = l.get("indicator", False)
            if cur_date == l["date"]:
                cur_move["line_ids"].append(
                    (0, 0, self._prepare_move_line_01(l, seq, indicator))
                )
                cur_move["line_ids"].append(
                    (0, 0, self._prepare_move_line_02(l, seq, indicator))
                )
            else:
                # new move
                if moves and not float_is_zero(cur_balance, precision_rounding=prec):
                    raise UserError(
                        self.env._(  # pylint: disable=translation-not-lazy
                            "The journal entry that ends on line %(line)d is not "
                            "balanced (balance is %(balance)s)."
                        )
                        % {"line": l["line"] - 1, "balance": cur_balance}
                    )
                if cur_move:
                    if len(cur_move["line_ids"]) <= 1:
                        raise UserError(
                            self.env._(  # pylint: disable=translation-not-lazy
                                "move should have more than 1 line num: %(line)s,"
                                "data : %(lines)s"
                            )
                            % {"line": l["line"], "lines": cur_move["line_ids"]}
                        )
                    moves.append(cur_move)
                cur_move = self._prepare_move(l)
                cur_move["line_ids"] = [
                    (0, 0, self._prepare_move_line_01(l, seq, indicator)),
                    (0, 0, self._prepare_move_line_02(l, seq, indicator)),
                ]
                cur_date = l["date"]
            cur_balance += l["credit"] - l["debit"]
        if cur_move:
            moves.append(cur_move)
        if not float_is_zero(cur_balance, precision_rounding=prec):
            raise UserError(
                self.env._(  # pylint: disable=translation-not-lazy
                    "The journal entry that ends on the last line is not "
                    "balanced (balance is %s)."
                )
                % cur_balance
            )
        rmoves = self.env["account.move"]
        for move in moves:
            created = amo.create(move)
            rmoves += created
        _logger.info(
            "Created %d account move(s) (IDs %s) via file import",
            len(rmoves),
            rmoves.ids,
        )
        if post:
            rmoves._post()
        return rmoves

    def _prepare_move(self, pivot_line):
        vals = {
            "journal_id": pivot_line["journal_id"],
            "ref": pivot_line.get("ref"),
            "date": pivot_line["date"],
        }
        return vals

    def _prepare_move_line_01(self, pivot_line, sequence, indicator):
        vals = {}
        has_taxes = pivot_line.get("tax_ids")
        if indicator == "S":
            amount = pivot_line["net_amount"] if has_taxes else pivot_line["debit"]
            vals.update({"credit": 0.0, "debit": amount})
        if indicator == "H":
            amount = pivot_line["net_amount"] if has_taxes else pivot_line["credit"]
            vals.update({"credit": amount, "debit": 0})
        if has_taxes:
            vals["tax_ids"] = [(6, 0, pivot_line["tax_ids"])]
        vals.update(
            {
                "name": pivot_line["name"],
                "account_id": pivot_line["account_id"],
                "import_external_id": "{}-{}".format(sequence, pivot_line.get("line")),
                "indicator": indicator,
                "analytic_distribution": {
                    pivot_line.get(analytic_account_id_field): 100.0
                    for analytic_account_id_field in (
                        "analytic_account_1_id",
                        "analytic_account_2_id",
                    )
                    if pivot_line.get(analytic_account_id_field)
                    and self.env["account.account"]
                    .browse(pivot_line["account_id"])
                    .account_type
                    in (
                        "income",
                        "expense",
                    )
                },
            }
        )
        return vals

    def _prepare_move_line_02(self, pivot_line, sequence, indicator):
        vals = {}
        has_contra_taxes = pivot_line.get("contra_tax_ids")
        if indicator == "S":
            amount = (
                pivot_line["contra_net_amount"]
                if has_contra_taxes
                else pivot_line["debit"]
            )
            vals.update({"credit": amount, "debit": 0})
        if indicator == "H":
            amount = (
                pivot_line["contra_net_amount"]
                if has_contra_taxes
                else pivot_line["credit"]
            )
            vals.update({"credit": 0, "debit": amount})
        if has_contra_taxes:
            vals["tax_ids"] = [(6, 0, pivot_line["contra_tax_ids"])]
        vals.update(
            {
                "name": pivot_line["name"],
                "account_id": pivot_line["contra_account_id"],
                "import_external_id": "{}-{}".format(sequence, pivot_line.get("line")),
                "indicator": indicator,
                "analytic_distribution": {
                    pivot_line.get(analytic_account_id_field): 100.0
                    for analytic_account_id_field in (
                        "analytic_account_1_id",
                        "analytic_account_2_id",
                    )
                    if pivot_line.get(analytic_account_id_field)
                    and self.env["account.account"]
                    .browse(pivot_line["contra_account_id"])
                    .account_type
                    in (
                        "income",
                        "expense",
                    )
                },
            }
        )
        return vals
