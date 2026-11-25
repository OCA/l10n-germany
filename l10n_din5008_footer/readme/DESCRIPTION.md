This glue module connects the DIN 5008 layout shipped with Odoo
(`l10n_din5008`) to the shared report footer of `l10n_de_report_footer`:

- the footer text, the company address block and the tagline are printed
  with the company placeholders rendered;
- the shared footer lines (German tax numbers and the lines added by other
  modules) are printed in the legal section of the footer, before the VAT
  number;
- for this layout the account holder of the bank accounts can be printed and
  the widths of the four footer columns can be set in the document layout;
- the bottom margin configured in the document layout applies to the DIN 5008
  reports (previously the module `l10n_din5008_report_margin_bottom`).

It is installed automatically when both modules are installed.
