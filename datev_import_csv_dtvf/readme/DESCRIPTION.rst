DATEV Format .csv Import
========================

The module "datev_import_csv_dtvf" enables the import of DATEV journal entries into Odoo.
Possible use cases include:

- DATEV journal entries from payroll and salary accounting
- DATEV journal entries in the context of annual financial statements
- DATEV journal entries in the context of reallocations by the tax consultant
- DATEV journal entries in the context of depreciation (AfA) bookings by the tax consultant
- DATEV journal entries in the context of loans

Currently, the following limitations exist:

- DATEV journal entries containing tax-related booking keys require adjustments in Odoo
- Under certain circumstances, DATEV journal entries on creditor and debtor accounts may also be affected.
