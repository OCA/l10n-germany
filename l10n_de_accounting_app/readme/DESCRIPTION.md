# OCA Accounting Add-ons — German Odoo Setup

A curated catalogue of the Odoo Community Association (OCA) modules we use to run a complete German accounting workflow on Odoo: dunning, bank statement import, DATEV exchange with the tax adviser, VAT return preparation, SEPA payments, and DIN 5008 compliant PDFs.

The list is organised by accounting function rather than by repository, so each section answers a single question — *"which module handles X?"* — and gives the OCA repo it lives in, with a short note on why we picked it (and where there are trade-offs between alternatives, what to weigh).

Everything listed here is either installed or qualified as the default choice for the corresponding need.

Reference: OCA's own *must-have accounting modules* list at <https://www.odoo-community.org/list-of-must-have-oca-accounting-modules>.

Each repository linked below lives under <https://github.com/OCA>. Module names are given without a version pin — use the branch matching your Odoo version.

---

## Invoice Import/Export EDI

Source: Odoo standard.

- **account_edi_ubl_cii** — Replaces the older OCA account_invoice_facturx, which is no longer needed.

## Followup (Mahnwesen)

From [OCA/credit-control](https://github.com/OCA/credit-control):

Two alternatives — pick by the feature you need.

- **account_invoice_overdue_reminder** — Advantage: handles credit notes.
- **account_credit_control** — Advantage: supports dunning fees (Mahngebühren).

## Reporting

From [OCA/l10n-germany](https://github.com/OCA/l10n-germany):

- **l10n_de_mis_reports** — Profit/Loss, Balance Sheet, SKR03, SKR04.

## Bank Import

From [OCA/bank-statement-import](https://github.com/OCA/bank-statement-import):

More connectors are available in the same repository.

- **account_statement_import_sheet_file** — CSV / Excel bank statement import.
- **account_statement_import_camt54** — CAMT.054 schema.
- **account_statement_import_online_paypal** — PayPal online statement fetching.
- **account_statement_import_online_ponto** — Ponto API, fetches statements automatically.
- **account_statement_import_online_stripe** — Stripe API, fetches statements automatically.

## DATEV

From [OCA/l10n-germany](https://github.com/OCA/l10n-germany):

**Workflow choice:**

- Tax adviser does **not** need PDFs → use `datev_export_dtvf` for everything.
- Tax adviser needs PDFs → use `datev_export_xml` (upload to DATEV Unternehmen Online) + `datev_export_dtvf` for the remaining journals.

- **datev_export_dtvf** — Exports all accounting entries in DTVF format. No PDF attachments.
- **datev_export_xml** — Exports bills/invoices with PDF attachment for upload to DATEV Unternehmen Online.
- **datev_import_csv_dtvf** — Imports accounting entries from DATEV. Mainly used for payroll postings (Lohnsteuer).

## VAT Report (USt-VA) + ZM

From [OCA/l10n-germany](https://github.com/OCA/l10n-germany):

- **l10n_de_tax_statement** — Produces a report for manual entry into ELSTER (no API connection).
- **l10n_de_tax_statement_zm** — Extension for the Zusammenfassende Meldung (intra-community).

## Payment

From [OCA/bank-payment](https://github.com/OCA/bank-payment):

- **account_payment_mode** — Payment modes.
- **account_payment_order** — Group outgoing payments into one order containing multiple vendor payments, for easy SEPA Credit XML generation.
- **account_banking_sepa_credit_transfer** — Required to create SEPA Credit files for vendor payments.
- **account_banking_sepa_direct_debit** — Required for SEPA direct debit (Bankeinzug).

## PDF Report

From [OCA/l10n-germany](https://github.com/OCA/l10n-germany):

- **l10n_din5008_move_name** — Adds the invoice number to the PDF subject line per DIN 5008.

## Nice to Have

From [OCA/account-financial-tools](https://github.com/OCA/account-financial-tools):

- **account_move_name_sequence** — Assign an own number sequence to each journal instead of the shared default.
