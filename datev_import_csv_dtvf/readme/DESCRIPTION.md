## DATEV Format .csv Import

The module "datev_import_csv_dtvf" enables the import of DATEV journal
entries into Odoo. Possible use cases include:

- DATEV journal entries from payroll and salary accounting
- DATEV journal entries in the context of annual financial statements
- DATEV journal entries in the context of reallocations by the tax
  consultant
- DATEV journal entries in the context of depreciation (AfA) bookings by
  the tax consultant
- DATEV journal entries in the context of loans

## Tax handling (Automatikkonten)

The import wizard supports automatic tax line generation based on
account default taxes. When the option "Apply Account Default Taxes" is
enabled, accounts configured with default taxes (Automatikkonten, e.g.
SKR03 account 4400 with 19% input VAT) will have their imported gross
amounts automatically split into net amount + tax lines by Odoo's tax
engine.

Currently, the following limitations exist:

- DATEV journal entries containing tax-related booking keys require
  attention. While there is an optional feature to implement tax handling
  it still needs careful attention to see if entries are created as intended in Odoo
- Under certain circumstances, DATEV journal entries on creditor and
  debtor accounts may also be affected.
