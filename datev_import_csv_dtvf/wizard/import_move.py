# Copyright 2012-2019 Akretion France (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from datetime import date as datelib, datetime
from tempfile import TemporaryFile

import unicodecsv

from odoo import _, fields, models
from odoo.exceptions import UserError
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

    def run_import(self):
        self.ensure_one()
        fileobj = TemporaryFile("wb+")
        file_bytes = base64.b64decode(self.file_to_import)
        fileobj.write(file_bytes)
        fileobj.seek(2)  # We must start reading 3rd line !
        pivot = self.genericcsv2pivot(fileobj)
        fileobj.close()
        _logger.debug("pivot before update: %s", pivot)
        self.clean_strip_pivot(pivot)
        self.update_pivot(pivot)
        moves = self.create_moves_from_pivot(pivot, post=self.post_move)
        action = {
            "name": _("Imported Journal Entries"),
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "nodestroy": False,
            "target": "current",
        }

        if len(moves) == 1:
            action.update(
                {
                    "view_mode": "form,tree",
                    "res_id": moves[0].id,
                }
            )
        else:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", moves.ids)],
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

    def genericcsv2pivot(self, fileobj):
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
        first_line = fileobj.readline().decode()
        dialect = unicodecsv.Sniffer().sniff(first_line)
        fileobj.seek(0)
        reader = unicodecsv.DictReader(
            fileobj,
            fieldnames=fieldnames,
            delimiter=dialect.delimiter,
            quotechar='"',
            quoting=unicodecsv.QUOTE_MINIMAL,
            encoding="ISO-8859-1",
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
                        (
                            _(
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

    def create_moves_from_pivot(self, pivot, post=False):  # noqa: C901
        _logger.debug("Final pivot: %s", pivot)
        amo = self.env["account.move"]
        company_id = self.env.company.id
        # Generate SPEED DICTS
        # account
        acc_speed_dict = {
            account["code"].upper(): account["id"]
            for account in self.env["account.account"].search_read(
                [("company_id", "=", company_id), ("deprecated", "=", False)], ["code"]
            )
        }
        # contra_account
        accc_speed_dict = acc_speed_dict.copy()
        # journal
        journal_speed_dict = {
            journal["code"].upper(): journal["id"]
            for journal in self.env["account.journal"].search_read(
                [("company_id", "=", company_id)], ["code"]
            )
        }
        # analytic account
        analytic_speed_dict = {
            (
                analytic_account["code"] or analytic_account["name"]
            ).upper(): analytic_account["id"]
            for analytic_account in self.env["account.analytic.account"].search_read(
                [("company_id", "=", company_id)], ["code", "name"]
            )
        }
        key2label = {
            "account": _("account codes"),
            "contra_account": _("contra account codes"),
            "journal": _("journal codes"),
            "analytic_account_1": _("analytic account codes"),
            "analytic_account_2": _("analytic account codes"),
        }
        errors = {"other": []}
        for key in key2label.keys():
            errors[key] = {}

        def match_account(line, speed_dict, id_field, code_field):
            if line[code_field] in speed_dict:
                line[id_field] = speed_dict[l[code_field]]
            if not line.get(id_field):
                # Match when import = 61100000 and Odoo has 611000
                acc_code_tmp = l[code_field]
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
                            "Approximate match: import account %s has been matched "
                            "with Odoo account %s" % (line[code_field], code)
                        )
                        line[id_field] = account_id
                        break
            if not line.get(id_field):
                errors[code_field].setdefault(line[code_field], []).append(l["line"])

        # MATCHES + CHECKS
        for l in pivot:  # noqa: E741
            assert l.get("line") and isinstance(
                l.get("line"), int
            ), "missing line number"
            # 1. account
            match_account(l, acc_speed_dict, "account_id", "account")
            # 2. contra_account
            match_account(l, accc_speed_dict, "contra_account_id", "contra_account")
            # 3. journal
            if l["journal"] in journal_speed_dict:
                l["journal_id"] = journal_speed_dict[l["journal"]]
            else:
                errors["journal"].setdefault(l["journal"], []).append(l["line"])
            # 4. name
            if not l.get("name"):
                errors["other"].append(_("Line %d: missing label.") % l["line"])
            # 5. date
            if not l.get("date"):
                errors["other"].append(_("Line %d: missing date.") % l["line"])
            else:
                if not isinstance(l.get("date"), datelib):
                    try:
                        l["date"] = datetime.strptime(l["date"], "%Y-%m-%d")
                    except Exception:
                        errors["other"].append(
                            _("Line %(line)d: bad date format %(date)s") % l
                        )
            # 6. credit
            if not isinstance(l.get("credit"), float):
                errors["other"].append(
                    _("Line %(line)d: bad value for credit (%(credit)s).") % l
                )
            # 7. debit
            if not isinstance(l.get("debit"), float):
                errors["other"].append(
                    _("Line %(line)d: bad value for debit (%(debit)s).") % l
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
        # LIST OF ERRORS
        msg = ""
        for key, label in key2label.items():
            if errors[key]:
                msg += _(
                    "List of %(label)s that don't exist in Odoo:\n%(codes)s\n\n"
                ) % {
                    "label": label,
                    "codes": "\n".join(
                        [
                            "- %(code)s : line(s) %(lines)s"
                            % {
                                "code": code,
                                "lines": ", ".join([str(i) for i in lines]),
                            }
                            for (code, lines) in errors[key].items()
                        ]
                    ),
                }
        if errors["other"]:
            msg += _("List of misc errors:\n%s") % (
                "\n".join(["- %s" % e for e in errors["other"]])
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
                        _(
                            "The journal entry that ends on line %(line)d is not "
                            "balanced (balance is %(balance)s)."
                        )
                        % {"line": l["line"] - 1, "balance": cur_balance}
                    )
                if cur_move:
                    if len(cur_move["line_ids"]) <= 1:
                        raise UserError(
                            _(
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
                _(
                    "The journal entry that ends on the last line is not "
                    "balanced (balance is %s)."
                )
                % cur_balance
            )
        rmoves = self.env["account.move"]
        for move in moves:
            rmoves += amo.create(move)
        _logger.info("Account moves IDs %s created via file import" % rmoves.ids)
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
        if indicator == "S":
            vals.update(
                {
                    "credit": 0.0,
                    "debit": pivot_line["debit"],
                }
            )
        if indicator == "H":
            vals.update({"credit": pivot_line["credit"], "debit": 0})
        vals.update(
            {
                "name": pivot_line["name"],
                "account_id": pivot_line["account_id"],
                "import_external_id": "%s-%s" % (sequence, pivot_line.get("line")),
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
        if indicator == "S":
            vals.update(
                {
                    "credit": pivot_line["debit"],
                    "debit": 0,
                }
            )
        if indicator == "H":
            vals.update(
                {
                    "credit": 0,
                    "debit": pivot_line["credit"],
                }
            )
        vals.update(
            {
                "name": pivot_line["name"],
                "account_id": pivot_line["contra_account_id"],
                "import_external_id": "%s-%s" % (sequence, pivot_line.get("line")),
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
