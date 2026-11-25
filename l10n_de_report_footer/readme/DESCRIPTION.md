This module is the common base for the German report footer. It provides the
company footer configuration that report layouts share, so that the standard
Odoo layouts, the DIN 5008 layout shipped with Odoo (`l10n_din5008`, through
`l10n_din5008_footer`) and `layout_din5008` print the same footer content.

- **Company placeholders**: the footer text, the address and the tagline of
  the document layout can contain company data (phone, e-mail, VAT, bank
  account, ...) inserted with the dynamic placeholder picker of the HTML
  editor (type `/` in the editor). The placeholders are rendered when a
  report is printed. With the module `html_editor_icon` (OCA/web) installed,
  the same texts offer an `/icon` command to insert Font Awesome pictograms,
  for example in front of the phone number or the e-mail address.
- **Footer lines**: the German tax numbers of the company (with `l10n_de`)
  are printed as switchable lines of the company block of every layout. A
  shared QWeb hook (`l10n_de_report_footer.footer_lines`) lets other modules
  add lines once for every layout.
- **Layout settings**: the settings of the document layout are stored in one
  JSON field of the company. Modules declare their settings in Python (key,
  type, default, range, section) and the document layout wizard renders them
  in tabs, with a live preview, without an own field or view per setting.
- **Bottom margin**: the bottom page margin of PDF reports can be increased
  in the document layout when the footer needs more space than the paper
  format reserves (previously the module `l10n_din5008_report_margin_bottom`).
- **Preview highlight**: while the address, the tagline, the footer text or a
  field of the document layout that changes a size or a margin is focused,
  the affected area is outlined in the preview.
