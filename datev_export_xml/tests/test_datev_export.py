# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2020, Elego Software Solutions GmbH, Berlin
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import io
import logging
import zipfile
from datetime import date, timedelta

from lxml import etree

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestDatevExport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.receivable = self.env.ref("account.data_account_type_receivable")
        self.income = self.env.ref("account.data_account_type_revenue")
        self.payable = self.env.ref("account.data_account_type_payable")
        self.expense = self.env.ref("account.data_account_type_expenses")
        self.JournalObj = self.env["account.journal"]
        self.sale_journal = self.JournalObj.search([("type", "=", "sale")])[0]
        self.purchase_journal = self.JournalObj.search([("type", "=", "purchase")])[0]
        self.AccountObj = self.env["account.account"]
        self.PartnerObj = self.env["res.partner"]
        self.AnalyticAccountObj = self.env["account.analytic.account"]
        self.ProductObj = self.env["product.product"]
        self.today = fields.Date.today()
        self.InvoiceObj = self.env["account.move"]
        self.InvoiceLineObj = self.env["account.move.line"]
        self.AttachmentObj = self.env["ir.attachment"]
        self.DatevExportObj = self.env["datev.export.xml"]

        self.inv_attach_de = self.env.ref("datev_export_xml.vendor_bill_attachment_DE")
        self.inv_attach_eu = self.env.ref("datev_export_xml.vendor_bill_attachment_EU")
        self.inv_attach_noneu = self.env.ref(
            "datev_export_xml.vendor_bill_attachment_NonEU"
        )

        self.refund_attach_de = self.env.ref(
            "datev_export_xml.bill_refund_attachment_DE"
        )
        self.refund_attach_eu = self.env.ref(
            "datev_export_xml.bill_refund_attachment_EU"
        )
        self.refund_attach_noneu = self.env.ref(
            "datev_export_xml.bill_refund_attachment_NonEU"
        )

        self.customer_de = self.env.ref("datev_export_xml.customer_DE")
        self.vendor_de = self.env.ref("datev_export_xml.vendor_DE")

        self.customer_eu = self.env.ref("datev_export_xml.customer_EU")
        self.vendor_eu = self.env.ref("datev_export_xml.vendor_EU")

        self.customer_noneu = self.env.ref("datev_export_xml.customer_NonEU")
        self.vendor_noneu = self.env.ref("datev_export_xml.vendor_NonEU")

        self.account_income = self.env.ref("datev_export_xml.account_datev_income")
        self.account_expense = self.env.ref("datev_export_xml.account_datev_expense")

        self.consulting = self.env.ref("datev_export_xml.product_datev_01")
        self.lease = self.env.ref("datev_export_xml.product_datev_02")

        self.analytic_account_it = self.env.ref(
            "datev_export_xml.analytic_account_datev_01"
        )
        self.analytic_account_office = self.env.ref(
            "datev_export_xml.analytic_account_datev_02"
        )

        self.parent_customer = self.env.ref("datev_export_xml.customer_parent")
        self.child_customer = self.env.ref("datev_export_xml.customer_child")

        # Ensure the initial state
        self.refund_date = self.today - timedelta(days=55)
        self.start_date = self.today - timedelta(days=34)
        self.end_date = self.today - timedelta(days=32)
        self.InvoiceObj.with_context(force_delete=True).search([]).unlink()
        self.env.company.datev_default_period = "week"

    def _check_filecontent(self, export):
        # check content only for single invoice
        # datev export based on unit test cases
        if not export.line_ids.attachment_id or not export.invoice_ids:
            return {}

        export.check_valid_data(export.invoice_ids)
        invoice = export.invoice_ids[0].name
        invoice = invoice.replace("/", "-")
        zip_data = base64.b64decode(export.line_ids.attachment_id.datas)
        fp = io.BytesIO()
        fp.write(zip_data)
        zipfile.is_zipfile(fp)
        file_list = set()
        invoice_xml = {}
        with zipfile.ZipFile(fp, "r") as z:
            for zf in z.namelist():
                file_list.add(zf)

            doc_file = "document.xml"
            inv_file = str(invoice + ".xml")
            doc_data = z.read(doc_file)
            inv_data = z.read(inv_file)
            # document.xml
            doc_root = etree.fromstring(doc_data)
            # invoice.xml file
            inv_root = etree.fromstring(inv_data)
            for i in inv_root:
                invoice_xml.update(i.attrib)

            return {
                "file_list": file_list,
                "zip_file": z,
                "document": lambda xpath: doc_root.find(
                    xpath, namespaces=doc_root.nsmap
                ),
                "invoice": lambda xpath: inv_root.find(
                    xpath, namespaces=inv_root.nsmap
                ),
            }

    def create_out_invoice(self, customer, start_date, end_date):
        # OUT Invoice
        tax = self.env["account.tax"].create(
            {
                "name": "Tax 0%",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        invoice = self.InvoiceObj.create(
            {
                "partner_id": customer.id,
                "user_id": self.env.user.id,
                "invoice_date": start_date,
                "invoice_date_due": end_date,
                "company_id": self.env.company.id,
                "currency_id": self.env.company.currency_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.consulting.id,
                            "quantity": 5.0,
                            "tax_ids": [(6, 0, tax.ids)],
                            "price_unit": 120.00,
                            "price_total": 600.0,
                            "credit": 600.0,
                            "debit": 0.0,
                            "account_id": self.account_income.id,
                            "analytic_account_id": self.analytic_account_it.id,
                        },
                    )
                ],
            }
        )
        invoice.invoice_line_ids.filtered("product_id")[0]
        self.assertEqual(invoice.state, "draft")
        invoice.action_post()
        return invoice

    def create_out_invoice_with_tax(self, customer, start_date, end_date, tax):
        # OUT Invoice with Tax 15%
        invoice = self.InvoiceObj.create(
            {
                "partner_id": customer.id,
                "user_id": self.env.user.id,
                "invoice_date": start_date,
                "invoice_date_due": end_date,
                "company_id": self.env.company.id,
                "currency_id": self.env.company.currency_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.consulting.id,
                            "quantity": 5.0,
                            "price_unit": 120.00,
                            "account_id": self.account_income.id,
                            "analytic_account_id": self.analytic_account_it.id,
                            "tax_ids": [(6, 0, tax.ids)],
                        },
                    ),
                ],
            }
        )
        invoice.invoice_line_ids.filtered("product_id")[0]
        self.assertEqual(invoice.state, "draft")
        invoice.action_post()
        return invoice

    def create_in_invoice(self, vendor, start_date, end_date):
        # IN Invoice
        tax = self.env["account.tax"].create(
            {
                "name": "Tax 0%",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        invoice = self.InvoiceObj.create(
            {
                "partner_id": vendor.id,
                "user_id": self.env.user.id,
                "invoice_date": start_date,
                "invoice_date_due": end_date,
                "company_id": self.env.company.id,
                "currency_id": self.env.company.currency_id.id,
                "move_type": "in_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.lease.id,
                            "quantity": 1.0,
                            "price_unit": 900.0,
                            "price_total": 900.0,
                            "credit": 0.0,
                            "debit": 900.0,
                            "tax_ids": [(6, 0, tax.ids)],
                            "account_id": self.account_expense.id,
                            "analytic_account_id": self.analytic_account_office.id,
                        },
                    ),
                ],
            }
        )
        self.assertEqual(invoice.state, "draft")
        invoice.action_post()
        return invoice

    def create_refund(self, invoice, refund_date):
        # OUT Refund/Credit Note
        refund = invoice._reverse_moves([{"invoice_date": refund_date}])
        self.assertEqual(refund.state, "draft")
        refund.action_post()
        return refund

    def create_customer_datev_export(self, start_date, end_date):
        datev_export = self.DatevExportObj.create(
            {
                "export_type": "out",
                "export_invoice": True,
                "export_refund": True,
                "check_xsd": True,
                "date_start": start_date,
                "date_stop": end_date,
            }
        )
        return datev_export

    def create_vendor_datev_export(self, start_date, end_date):
        datev_export = self.DatevExportObj.create(
            {
                "export_type": "in",
                "export_invoice": True,
                "export_refund": True,
                "check_xsd": True,
                "date_start": start_date,
                "date_stop": end_date,
            }
        )
        return datev_export

    def create_customer_datev_export_manually(self, invoice):
        start_date = invoice.invoice_date
        end_date = invoice.invoice_date_due
        datev_export = self.DatevExportObj.create(
            {
                "export_type": "out",
                "export_invoice": True,
                "export_refund": True,
                "check_xsd": True,
                "date_start": start_date,
                "date_stop": end_date,
                "manually_document_selection": True,
                "invoice_ids": [(6, 0, [invoice.id])],
            }
        )
        return datev_export

    def update_attachment(self, attachment, invoice):
        attachment.write(
            {
                "res_model": "account.invoice",
                "res_id": invoice.id,
            }
        )
        return attachment

    def _run_test_document(self, doc, invoice):
        inv_number = invoice.name.replace("/", "-")
        self.assertEqual(doc(".//header/clientName").text, invoice.company_id.name)
        self.assertEqual(doc(".//document/description").text, invoice.name)
        self.assertEqual(
            doc(".//extension[@datafile]").attrib["datafile"], inv_number + ".xml"
        )
        self.assertEqual(doc(".//extension[@name]").attrib["name"], inv_number + ".pdf")

        self.assertEqual(
            doc(".//property[@key='InvoiceType']").attrib["value"],
            "Outgoing" if invoice.move_type.startswith("out_") else "Incoming",
        )

    def _run_test_invoice(self, doc, invoice):
        inv_line = invoice.invoice_line_ids.filtered("product_id")[0]

        info = doc(".//invoice_info").attrib
        line = doc(".//invoice_item_list").attrib
        total = doc(".//total_amount").attrib

        self.assertEqual(
            info["invoice_type"],
            "Rechnung"
            if invoice.move_type.endswith("_invoice")
            else "Gutschrift/Rechnungskorrektur",
        )
        self.assertEqual(info["invoice_date"], invoice.invoice_date.isoformat())

        if invoice.move_type.startswith("out_"):
            self.assertEqual(
                doc(".//invoice_party/address").attrib["name"],
                invoice.partner_id.display_name,
            )
        else:
            self.assertEqual(
                doc(".//supplier_party/address").attrib["name"],
                invoice.partner_id.display_name,
            )

        self.assertEqual(float(line["quantity"]), inv_line.quantity)
        self.assertEqual(line["product_id"], inv_line.product_id.default_code)

        sign = -1 if invoice.move_type.endswith("_refund") else 1
        self.assertEqual(
            float(total["net_total_amount"]),
            sign * invoice.amount_untaxed,
        )
        self.assertEqual(
            float(total["total_gross_amount_excluding_third-party_collection"]),
            sign * invoice.amount_total,
        )
        # partner has bank account
        if invoice.partner_id.bank_ids:
            bank = doc(".//invoice_party/account").attrib
            self.assertEqual(
                bank["bank_name"], invoice.partner_id.bank_ids[0].bank_name
            )
            self.assertEqual(
                bank["iban"],
                invoice.partner_id.bank_ids[0].acc_number.replace(" ", ""),
            )

    def _run_test_out_refund_datev_export(self, refund):
        line = refund.invoice_line_ids.filtered("product_id")[0]
        self.assertEqual(refund.move_type, "out_refund")
        self.assertEqual(line.account_id, self.account_income)
        self.assertEqual(line.price_unit, 120.00)
        self.assertEqual(line.quantity, 5.00)
        self.assertEqual(refund.journal_id, self.sale_journal)
        self.assertEqual(refund.state, "posted")

        start_date = refund.invoice_date
        end_date = refund.invoice_date_due
        datev_export = self.create_customer_datev_export(start_date, end_date)
        self.assertFalse(datev_export.line_ids.attachment_id)
        self.assertEqual(
            datev_export.client_number,
            self.env.company.datev_client_number,
        )
        self.assertEqual(
            datev_export.consultant_number,
            self.env.company.datev_consultant_number,
        )
        self.assertEqual(datev_export.state, "draft")
        # There is always a first invoice
        self.assertEqual(datev_export.invoices_count, 1)
        invoice = datev_export.invoice_ids[0]
        self.assertEqual(invoice, refund)
        inv_number = invoice.name.replace("/", "-")

        self.assertEqual(datev_export.state, "draft")
        datev_export.action_pending()
        self.assertEqual(datev_export.state, "pending")
        datev_export.with_user(datev_export.create_uid.id).get_zip()
        datev_export._create_activity()
        datev_export.line_ids._compute_filesize()
        self.assertTrue(datev_export.line_ids.filesize)
        self.assertEqual(datev_export.state, "done")

        self.assertTrue(datev_export.line_ids.attachment_id)
        file_list = {"document.xml", inv_number + ".xml", inv_number + ".pdf"}
        res = self._check_filecontent(datev_export)
        # check list of files
        self.assertEqual(res["file_list"], file_list)
        # check document.xml
        self._run_test_document(res["document"], invoice)

        # check invoice.xml file
        self._run_test_invoice(res["invoice"], invoice)

    def _run_test_in_refund_datev_export(self, refund, attachment):
        line = refund.invoice_line_ids.filtered("product_id")[0]
        self.assertEqual(refund.move_type, "in_refund")
        self.assertEqual(line.account_id, self.account_expense)
        self.assertEqual(line.price_unit, 900.00)
        self.assertEqual(line.quantity, 1.00)
        self.assertEqual(refund.journal_id, self.purchase_journal)
        self.assertEqual(refund.state, "posted")

        start_date = refund.invoice_date
        end_date = refund.invoice_date_due
        datev_export = self.create_vendor_datev_export(start_date, end_date)

        attachment = self.update_attachment(attachment, refund)
        self.assertFalse(datev_export.line_ids.attachment_id)
        self.assertEqual(
            datev_export.client_number,
            self.env.company.datev_client_number,
        )
        self.assertEqual(
            datev_export.consultant_number,
            self.env.company.datev_consultant_number,
        )
        self.assertEqual(datev_export.state, "draft")
        # There is always a first invoice
        self.assertEqual(datev_export.invoices_count, 1)
        invoice = datev_export.invoice_ids[0]
        self.assertEqual(invoice, refund)
        inv_number = invoice.name.replace("/", "-")

        self.assertEqual(datev_export.state, "draft")
        datev_export.action_pending()
        self.assertEqual(datev_export.state, "pending")
        datev_export.with_user(datev_export.create_uid.id).get_zip()
        datev_export._create_activity()
        # self.DatevExportObj.cron_run_pending_export()
        # self.DatevExportObj.refresh()
        self.assertEqual(datev_export.state, "done")

        self.assertTrue(datev_export.line_ids.attachment_id)
        file_list = {"document.xml", f"{inv_number}.xml", f"{inv_number}.pdf"}
        res = self._check_filecontent(datev_export)
        # check list of files
        self.assertEqual(res["file_list"], file_list)
        # check document.xml
        self._run_test_document(res["document"], invoice)

        # check invoice.xml file
        self._run_test_invoice(res["invoice"], invoice)

    def _run_test_out_invoice_datev_export(self, invoice):
        line = invoice.invoice_line_ids.filtered("product_id")[0]
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(line.account_id, self.account_income)
        self.assertEqual(line.price_unit, 120.00)
        self.assertEqual(line.quantity, 5.00)
        self.assertEqual(invoice.journal_id, self.sale_journal)
        self.assertEqual(invoice.state, "posted")

        start_date = invoice.invoice_date
        end_date = invoice.invoice_date_due
        datev_export = self.create_customer_datev_export(start_date, end_date)
        self.assertFalse(datev_export.line_ids.attachment_id)
        self.assertEqual(
            datev_export.client_number,
            self.env.company.datev_client_number,
        )
        self.assertEqual(
            datev_export.consultant_number,
            self.env.company.datev_consultant_number,
        )
        self.assertEqual(datev_export.state, "draft")
        # There is always a first invoice
        self.assertEqual(datev_export.invoices_count, 1)
        invoice = datev_export.invoice_ids[0]
        self.assertEqual(invoice, invoice)
        inv_number = invoice.name.replace("/", "-")

        self.assertEqual(datev_export.state, "draft")
        datev_export.action_pending()
        self.assertEqual(datev_export.state, "pending")
        datev_export.with_user(datev_export.create_uid.id).get_zip()
        datev_export._create_activity()
        # self.DatevExportObj.cron_run_pending_export()
        # self.DatevExportObj.refresh()
        self.assertEqual(datev_export.state, "done")

        self.assertTrue(datev_export.line_ids.attachment_id)
        file_list = {"document.xml", inv_number + ".xml", inv_number + ".pdf"}
        res = self._check_filecontent(datev_export)
        # check list of files
        self.assertEqual(res["file_list"], file_list)
        # check document.xml
        self._run_test_document(res["document"], invoice)

        # check invoice.xml file
        self._run_test_invoice(res["invoice"], invoice)

    def _run_test_in_invoice_datev_export(self, invoice, attachment):
        line = invoice.invoice_line_ids.filtered("product_id")[0]
        self.assertEqual(invoice.move_type, "in_invoice")
        self.assertEqual(line.account_id, self.account_expense)
        self.assertEqual(line.price_unit, 900.00)
        self.assertEqual(line.quantity, 1.00)
        self.assertEqual(invoice.journal_id, self.purchase_journal)
        self.assertEqual(invoice.state, "posted")

        start_date = invoice.invoice_date
        end_date = invoice.invoice_date_due
        datev_export = self.create_vendor_datev_export(start_date, end_date)

        attachment = self.update_attachment(attachment, invoice)
        self.assertFalse(datev_export.line_ids.attachment_id)
        self.assertEqual(
            datev_export.client_number,
            self.env.company.datev_client_number,
        )
        self.assertEqual(
            datev_export.consultant_number,
            self.env.company.datev_consultant_number,
        )
        self.assertEqual(datev_export.state, "draft")
        self.assertEqual(datev_export.invoices_count, 1)
        invoice = datev_export.invoice_ids[0]
        self.assertEqual(invoice, invoice)
        inv_number = invoice.name.replace("/", "-")

        self.assertEqual(datev_export.state, "draft")
        datev_export.action_pending()
        self.assertEqual(datev_export.state, "pending")
        datev_export.with_user(datev_export.create_uid.id).get_zip()
        datev_export._create_activity()
        # self.DatevExportObj.cron_run_pending_export()
        # self.DatevExportObj.refresh()
        self.assertEqual(datev_export.state, "done")

        self.assertTrue(datev_export.line_ids.attachment_id)
        file_list = {"document.xml", f"{inv_number}.xml", f"{inv_number}.pdf"}
        res = self._check_filecontent(datev_export)
        # check list of files
        self.assertEqual(res["file_list"], file_list)
        # check document.xml
        self._run_test_document(res["document"], invoice)

        # check invoice.xml file
        self._run_test_invoice(res["invoice"], invoice)

    def _run_test_out_inv_datev_export_manually(self, invoice):
        line = invoice.invoice_line_ids.filtered("product_id")[0]
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(line.account_id, self.account_income)
        self.assertEqual(line.price_unit, 120.00)
        self.assertEqual(line.quantity, 5.00)
        self.assertEqual(invoice.journal_id, self.sale_journal)
        self.assertEqual(invoice.state, "posted")

        datev_export = self.create_customer_datev_export_manually(invoice)
        self.assertFalse(datev_export.line_ids.attachment_id)
        self.assertEqual(
            datev_export.client_number,
            self.env.company.datev_client_number,
        )
        self.assertEqual(
            datev_export.consultant_number,
            self.env.company.datev_consultant_number,
        )
        self.assertEqual(datev_export.state, "draft")
        self.assertEqual(datev_export.invoices_count, 1)
        invoice = datev_export.invoice_ids[0]
        self.assertEqual(invoice, invoice)
        inv_number = invoice.name.replace("/", "-")

        self.assertEqual(datev_export.state, "draft")
        datev_export.action_pending()
        self.assertEqual(datev_export.state, "pending")
        # manually do export via button : 'Create DATEV Export File'
        datev_export.with_user(datev_export.create_uid.id).with_context(
            {"datev_mode": "datev_export"}
        ).export_zip()
        self.assertEqual(datev_export.state, "done")
        self.assertTrue(datev_export.line_ids.attachment_id)
        file_list = {"document.xml", inv_number + ".xml", inv_number + ".pdf"}
        res = self._check_filecontent(datev_export)
        # check list of files
        self.assertEqual(res["file_list"], file_list)
        # check document.xml
        self._run_test_document(res["document"], invoice)

        # check invoice.xml file
        self._run_test_invoice(res["invoice"], invoice)

    # ------- CUSTOMER --------
    def test_01_out_invoice_de_datev_export(self):
        # 1. OUT Invoice DE
        invoice = self.create_out_invoice(
            self.customer_de, self.start_date, self.end_date
        )
        self._run_test_out_invoice_datev_export(invoice)

    def test_02_out_invoice_eu_datev_export(self):
        # 2. OUT Invoice EU
        invoice = self.create_out_invoice(
            self.customer_eu, self.start_date, self.end_date
        )
        self._run_test_out_invoice_datev_export(invoice)

    def test_03_out_invoice_noneu_datev_export(self):
        # 3. OUT Invoice NonEU
        invoice = self.create_out_invoice(
            self.customer_noneu, self.start_date, self.end_date
        )
        self._run_test_out_invoice_datev_export(invoice)

    def test_04_out_refund_de_datev_export(self):
        # 4. OUT Refund DE
        # before the due date of invoice
        invoice = self.create_out_invoice(
            self.customer_de, self.start_date, self.end_date
        )
        refund = self.create_refund(invoice, self.refund_date)
        self.assertEqual(refund.reversed_entry_id, invoice)
        self.assertEqual(refund.invoice_date, self.refund_date)
        self._run_test_out_refund_datev_export(refund)

    def test_05_out_refund_eu_datev_export(self):
        # 5. OUT Refund EU
        # before the due date of invoice
        invoice = self.create_out_invoice(
            self.customer_eu, self.start_date, self.end_date
        )
        refund = self.create_refund(invoice, self.refund_date)
        self.assertEqual(refund.reversed_entry_id, invoice)
        self.assertEqual(refund.invoice_date, self.refund_date)
        self._run_test_out_refund_datev_export(refund)

    def test_06_out_refund_noneu_datev_export(self):
        # 6. OUT Refund NonEU
        # before the due date of invoice
        invoice = self.create_out_invoice(
            self.customer_noneu, self.start_date, self.end_date
        )
        refund = self.create_refund(invoice, self.refund_date)
        self.assertEqual(refund.reversed_entry_id, invoice)
        self.assertEqual(refund.invoice_date, self.refund_date)
        self._run_test_out_refund_datev_export(refund)

    # ------- VENDOR --------
    def test_07_in_invice_de_datev_export(self):
        # 7. IN Invoice DE
        invoice = self.create_in_invoice(self.vendor_de, self.start_date, self.end_date)
        self._run_test_in_invoice_datev_export(invoice, self.inv_attach_de)

    def test_08_in_invoice_eu_datev_export(self):
        # 8. IN Invoice EU
        invoice = self.create_in_invoice(self.vendor_eu, self.start_date, self.end_date)
        self._run_test_in_invoice_datev_export(invoice, self.inv_attach_eu)

    def test_09_in_invoice_noneu_datev_export(self):
        # 9. IN Invoice NonEU
        invoice = self.create_in_invoice(
            self.vendor_noneu, self.start_date, self.end_date
        )
        self._run_test_in_invoice_datev_export(invoice, self.inv_attach_noneu)

    def test_10_in_refund_de_datev_export(self):
        # 10. IN Refund DE
        # before the due date of invoice
        invoice = self.create_in_invoice(self.vendor_de, self.start_date, self.end_date)
        refund = self.create_refund(invoice, self.refund_date)
        self.assertEqual(refund.reversed_entry_id, invoice)
        self.assertEqual(refund.invoice_date, self.refund_date)
        self._run_test_in_refund_datev_export(refund, self.refund_attach_de)

    def test_11_in_refund_eu_datev_export(self):
        # 11. IN Refund EU
        # before the due date of invoice
        invoice = self.create_in_invoice(self.vendor_eu, self.start_date, self.end_date)
        refund = self.create_refund(invoice, self.refund_date)
        self.assertEqual(refund.reversed_entry_id, invoice)
        self.assertEqual(refund.invoice_date, self.refund_date)
        self._run_test_in_refund_datev_export(refund, self.refund_attach_eu)

    def test_12_in_refund_noneu_datev_export(self):
        # 12. IN Refund NonEU
        # before the due date of invoice
        invoice = self.create_in_invoice(
            self.vendor_noneu, self.start_date, self.end_date
        )
        refund = self.create_refund(invoice, self.refund_date)
        self.assertEqual(refund.reversed_entry_id, invoice)
        self.assertEqual(refund.invoice_date, self.refund_date)
        self._run_test_in_refund_datev_export(refund, self.refund_attach_noneu)

    def test_13_out_invoice_with_tax(self):
        # OUT Invoice with tax
        self.InvoiceObj.with_context(force_delete=True).search([]).unlink()
        self.env.user.company_id.tax_calculation_rounding_method = "round_globally"
        tax = self.env["account.tax"].create(
            {
                "name": "Tax 15.0",
                "amount": 15.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        invoice = self.create_out_invoice_with_tax(
            self.child_customer, self.start_date, self.end_date, tax
        )
        self._run_test_out_invoice_datev_export(invoice)

    def test_14_datev_export_without_invoice(self):
        date_start = self.today - timedelta(days=self.today.weekday(), weeks=1)
        date_stop = date_start + timedelta(days=6)
        # 1. when export_invoice,export_refund are False
        # ValidationError: "You need to choose which documents types
        # (Invoices/Refunds) you want to export!"
        with self.assertRaises(ValidationError):
            datev_export = self.DatevExportObj.create(
                {
                    "export_type": "out",
                    "export_invoice": False,
                    "export_refund": False,
                }
            )
        # 2. when default values are set
        # date_start, date_end (based on datev_default_period of current company)
        # export_invoice = True,
        # export_refund = True,
        # check_xsd = True,
        # manually_document_selection = Flase
        datev_export = self.DatevExportObj.create(
            {
                "export_type": "out",
            }
        )
        self.assertFalse(datev_export.line_ids.attachment_id)
        self.assertEqual(
            datev_export.client_number,
            self.env.company.datev_client_number,
        )
        self.assertEqual(
            datev_export.consultant_number,
            self.env.company.datev_consultant_number,
        )
        self.assertEqual(datev_export.state, "draft")
        self.assertEqual(datev_export.date_start, date_start)
        self.assertEqual(datev_export.date_stop, date_stop)
        # change date_stop , so that incoice_count = 0
        datev_export.date_stop = date_stop - timedelta(4)
        self.assertEqual(datev_export.invoices_count, 0)
        # 3. when try to set state = 'pending' and invoice_count = 0
        # ValidationError: "No invoices/refunds for export!"
        with self.assertRaises(ValidationError):
            datev_export.action_pending()

    def test_15_datev_export_with_manually_document_selection(self):
        # OUT Invoice
        invoice = self.create_out_invoice(
            self.customer_de, self.start_date, self.end_date
        )
        self._run_test_out_inv_datev_export_manually(invoice)

    def test_16_manual_export(self):
        out_invoice = self.create_out_invoice(
            self.customer_de, self.start_date, self.end_date
        )

        self.DatevExportObj.with_context(
            active_model="account.move",
            active_ids=out_invoice.ids,
        ).export_zip_invoice()

        in_invoice = self.create_in_invoice(
            self.customer_de, self.start_date, self.end_date
        )

        self.DatevExportObj.export_zip_invoice(in_invoice.ids)

        with self.assertRaises(UserError):
            self.DatevExportObj.export_zip_invoice(in_invoice.ids + out_invoice.ids)

    def test_period(self):
        checks = [
            ("day", (2022, 6, 15), (2022, 6, 14), (2022, 6, 14)),
            ("week", (2022, 6, 15), (2022, 6, 6), (2022, 6, 12)),
            ("month", (2022, 6, 15), (2022, 5, 1), (2022, 5, 31)),
            ("year", (2022, 6, 15), (2021, 1, 1), (2021, 12, 31)),
            (False, (2022, 6, 15), (2022, 6, 14), (2022, 6, 14)),
        ]
        for dates in checks:
            today, start, stop = [date(*x) for x in dates[1:]]
            self.env.company.datev_default_period = dates[0]
            self.assertEqual(self.DatevExportObj._default_start(today), start)
            self.assertEqual(self.DatevExportObj._default_stop(today), stop)

    def test_state_workflow(self):
        in_invoice = self.create_in_invoice(
            self.customer_de, self.start_date, self.end_date
        )
        export = self.DatevExportObj.create(
            {
                "invoice_ids": [(6, 0, in_invoice.ids)],
                "export_type": "in",
                "manually_document_selection": True,
            }
        )

        self.assertTrue(export.invoice_ids)

        self.assertEqual(export.state, "draft")
        export.action_pending()
        self.assertEqual(export.state, "pending")
        export.action_draft()
        self.assertEqual(export.state, "draft")

        export.state = "running"
        with self.assertRaises(ValidationError):
            export.action_pending()
        with self.assertRaises(ValidationError):
            export.action_draft()

        export.action_done()
        self.assertEqual(export.state, "done")
