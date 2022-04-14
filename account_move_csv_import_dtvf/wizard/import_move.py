# Copyright 2012-2019 Akretion France (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime, date as datelib
import unicodecsv
from tempfile import TemporaryFile
import base64
import logging

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
    file_format = fields.Selection(
        [("genericcsv", "Generic CSV")],
        string="File Format",
        required=True,
        help="Select the type of file you are importing.",
    )
    file_encoding = fields.Selection(
        [
            ("utf-8", "UTF-8"),
            ("windows-1252", "Western (Windows-1252)"),
        ],
        string="File Encoding",
        default="utf-8",
    )
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
        for l in pivot:
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
        for l in pivot:
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
        for l in reader:
            i += 1
            if i == 1 and l["discount"]:
                year_str = l["discount"][0:4]
            if i >= 3:
                date_str = l["date"][0:2] + "/" + l["date"][-2:] + "/" + year_str
                try:
                    date = datetime.strptime(date_str, self.date_format)
                except Exception:
                    raise UserError(
                        (_("time data : '%s' in line %s does not match format '%s"))
                        % (date_str, i, self.date_format)
                    )
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
                }
                res.append(vals)
        return res

    def create_moves_from_pivot(self, pivot, post=False):
        _logger.debug("Final pivot: %s", pivot)
        amo = self.env["account.move"]
        company_id = self.env.user.company_id.id
        # Generate SPEED DICTS
        # account
        acc_speed_dict = {}
        acc_sr = self.env["account.account"].search_read(
            [("company_id", "=", company_id), ("deprecated", "=", False)], ["code"]
        )
        for l in acc_sr:
            acc_speed_dict[l["code"].upper()] = l["id"]
        # contra_account
        accc_speed_dict = {}
        accc_sr = self.env["account.account"].search_read(
            [("company_id", "=", company_id), ("deprecated", "=", False)], ["code"]
        )
        for l in accc_sr:
            accc_speed_dict[l["code"].upper()] = l["id"]
        # journal
        journal_speed_dict = {}
        journal_sr = self.env["account.journal"].search_read(
            [("company_id", "=", company_id)], ["code"]
        )
        for l in journal_sr:
            journal_speed_dict[l["code"].upper()] = l["id"]
        key2label = {
            "account": _("account codes"),
            "contra_account": _("contra account codes"),
            "journal": _("journal codes"),
        }
        errors = {"other": []}
        for key in key2label.keys():
            errors[key] = {}
        # MATCHES + CHECKS
        for l in pivot:
            assert l.get("line") and isinstance(
                l.get("line"), int
            ), "missing line number"
            # 1. account
            if l["account"] in acc_speed_dict:
                l["account_id"] = acc_speed_dict[l["account"]]
            if not l.get("account_id"):
                # Match when import = 61100000 and Odoo has 611000
                acc_code_tmp = l["account"]
                while acc_code_tmp and acc_code_tmp[-1] == "0":
                    acc_code_tmp = acc_code_tmp[:-1]
                    if acc_code_tmp and acc_code_tmp in acc_speed_dict:
                        l["account_id"] = acc_speed_dict[acc_code_tmp]
                        break
            if not l.get("account_id"):
                # Match when import = 611000 and Odoo has 611000XX
                for code, account_id in acc_speed_dict.items():
                    if code.startswith(l["account"]):
                        _logger.warning(
                            "Approximate match: import account %s has been matched "
                            "with Odoo account %s" % (l["account"], code)
                        )
                        l["account_id"] = account_id
                        break
            if not l.get("account_id"):
                errors["account"].setdefault(l["account"], []).append(l["line"])
            # 2. contra_account
            if l["contra_account"] in accc_speed_dict:
                l["contra_account_id"] = accc_speed_dict[l["contra_account"]]
            if not l.get("contra_account_id"):
                # Match when import = 61100000 and Odoo has 611000
                accc_code_tmp = l["contra_account"]
                while accc_code_tmp and accc_code_tmp[-1] == "0":
                    accc_code_tmp = accc_code_tmp[:-1]
                    if accc_code_tmp and accc_code_tmp in accc_speed_dict:
                        l["contra_account_id"] = accc_speed_dict[accc_code_tmp]
                        break
            if not l.get("contra_account_id"):
                # Match when import = 611000 and Odoo has 611000XX
                for code, contra_account_id in accc_speed_dict.items():
                    if code.startswith(l["contra_account"]):
                        _logger.warning(
                            "Approximate match: import account %s has been matched "
                            "with Odoo account %s" % (l["contra_account"], code)
                        )
                        l["contra_account_id"] = contra_account_id
                        break
            if not l.get("contra_account_id"):
                errors["contra_account"].setdefault(l["contra_account"], []).append(
                    l["line"]
                )
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
                            _("Line %d: bad date format %s") % (l["line"], l["date"])
                        )
            # 6. credit
            if not isinstance(l.get("credit"), float):
                errors["other"].append(
                    _("Line %d: bad value for credit (%s).") % (l["line"], l["credit"])
                )
            # 7. debit
            if not isinstance(l.get("debit"), float):
                errors["other"].append(
                    _("Line %d: bad value for debit (%s).") % (l["line"], l["debit"])
                )
            # test that they don't have both a value
        # LIST OF ERRORS
        msg = ""
        for key, label in key2label.items():
            if errors[key]:
                msg += _("List of %s that don't exist in Odoo:\n%s\n\n") % (
                    label,
                    "\n".join(
                        [
                            "- %s : line(s) %s"
                            % (code, ", ".join([str(i) for i in lines]))
                            for (code, lines) in errors[key].items()
                        ]
                    ),
                )
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
        prec = self.env.user.company_id.currency_id.rounding
        seq = self.env["ir.sequence"].next_by_code("account.move.import")
        cur_move = {}
        for l in pivot:
            indicator = l.get("indicator", False)
            if cur_date == l["date"]:
                cur_move["line_ids"].append(
                    (0, 0, self._prepare_move_line_02(l, seq, indicator))
                )
                cur_move["line_ids"].append(
                    (0, 0, self._prepare_move_line_01(l, seq, indicator))
                )
            else:
                # new move
                if moves and not float_is_zero(cur_balance, precision_rounding=prec):
                    raise UserError(
                        _(
                            "The journal entry that ends on line %d is not "
                            "balanced (balance is %s)."
                        )
                        % (l["line"] - 1, cur_balance)
                    )
                if cur_move:
                    if len(cur_move["line_ids"]) <= 1:
                        raise UserError(
                            _("move should have more than 1 line num: %s," "data : %s")
                            % (l["line"], cur_move["line_ids"])
                        )
                    moves.append(cur_move)
                cur_move = self._prepare_move(l)
                cur_move["line_ids"] = [
                    (0, 0, self._prepare_move_line_02(l, seq, indicator)),
                    (0, 0, self._prepare_move_line_01(l, seq, indicator)),
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
            rmoves.post()
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
                    "credit": pivot_line["credit"],
                    "debit": 0.0,
                }
            )
        if indicator == "H":
            vals.update({"credit": 0.0, "debit": pivot_line["debit"]})
        vals.update(
            {
                "name": pivot_line["name"],
                "account_id": pivot_line["account_id"],
                "import_external_id": "%s-%s" % (sequence, pivot_line.get("line")),
                "indicator": indicator,
            }
        )
        return vals

    def _prepare_move_line_02(self, pivot_line, sequence, indicator):
        vals = {}
        if indicator == "S":
            vals.update(
                {
                    "credit": 0.0,
                    "debit": pivot_line["debit"],
                }
            )
        if indicator == "H":
            vals.update(
                {
                    "credit": pivot_line["debit"],
                    "debit": 0.0,
                }
            )
        vals.update(
            {
                "name": pivot_line["name"],
                "account_id": pivot_line["contra_account_id"],
                "import_external_id": "%s-%s" % (sequence, pivot_line.get("line")),
                "indicator": indicator,
            }
        )
        return vals
