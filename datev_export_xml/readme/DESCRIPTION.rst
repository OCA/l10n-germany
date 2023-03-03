Odoo Export to DATEV XML
========================

The datev_export_xml module allows to export invoices and bills with their origin digitized receipts
in order to transmitt structured accounting data via file-based DATEV XML format. The transfer of these files created by this module to the invoice books in DATEV Unternehmen Online can be done currently via the free DATEV document transfer app.

The DATEV XML interface cannot cover use cases such as:

- Pure G/L account postings (G/L account to G/L account, e.g. payment postings)
- Master data transfer for business partners (customers/creditors)
- certain §13b UStG issues (see permissible tax codes for DATEV Unternehmen online)
