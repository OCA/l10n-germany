Go to *Settings > Companies > Configure Document Layout* and choose
**DIN 5008 Form A** or **DIN 5008 Form B**. The matching paper format
(*DIN 5008 Form A* / *DIN 5008 Form B*) is selected automatically.

The layout settings below the paper format show four tabs once a DIN 5008
layout is selected: three tabs of this layout and the tab *Footer* of the
module `l10n_de_report_footer`; the bottom margin of that module (tab *Page*
of the other layouts) is offered in the tab *Positions (mm)*. Every change
is shown in the preview at once.

Tab **DIN 5008 Document**:

- **Document Information**: where the document information of the standard
  reports (dates, references, salesperson, ...) is printed. *Below the title*
  keeps the standard position. *Beside the address* (default) moves the block
  into the DIN 5008 information block next to the address window. The block is moved
  after rendering, so extensions adding rows to it keep working; only styles
  that rely on its original position do not apply.
- **Logo Position**: print the company logo on the left or on the right of
  the letterhead; the tagline is printed on the opposite side.
- **Logo Height (mm)**: maximum height of the logo, 0 keeps the height of
  the layout (15 mm for Form A, 30 mm for Form B).
- **Address Font Scale**: scale factor of the recipient address font
  (1 = 10 pt); the line height follows.
- **Fold Marks** and **Hole Mark**: print the fold marks and the hole mark
  on every page.

Tab **Sender Line**:

- **Print Sender Line**: print the *Address* text of the document layout as a
  single line above the recipient address (Rücksendeangabe); its lines are
  joined with the **Separator**: type any character(s) or pick one of the
  presets (`|`, `•`, `·`) from the list next to the field. **Separator Gap
  (mm)** adds space on both sides of every separator and **Separator Font
  Scale** prints the separators smaller or larger than the 7 pt sender line.
  The address may contain placeholders; the placeholder *DIN 5008 Sender
  Line Text* provides the company name and address formatted with the
  separator and the **Country** option (country code before the postal code,
  `DE-12345 Berlin`, or the country name at the end). Without address text
  the formatted company address is printed.

Tab **Positions (mm)**:

- **Address Window Offset** and **Address Window Height**: vertical offset of
  the address row relative to the DIN 5008 position and its minimum height.
- **Remark Zone Height**: height of the remark zone (Zusatz- und Vermerkzone)
  between the sender line and the recipient address. DIN 5008 reserves
  12.7 mm for remarks such as "Einschreiben"; the default of 0 mm prints the
  recipient address directly below the sender line.
- **Information Block Left** and **Information Block Width**: distance from
  the left edge and width of the column next to the address window.
- **Bottom Margin**: bottom page margin reserved for the footer of the PDF
  reports, 0 keeps the margin of the paper format (setting of the module
  `l10n_de_report_footer`, key `page.margin_bottom`).

Tab **Footer** (module `l10n_de_report_footer`, with `l10n_de`): print the
tax number and the business identification number of the company as lines
of the legal block of the footer, next to the page number.

While one of the position fields is focused, the affected area is outlined
in the preview. Clear a numeric field to restore
its default. The settings are stored in the field *Report Layout
Configuration* of the company (`report_layout_config`, keys `din5008.*`).
The footer text with company placeholders, the shared footer lines and the
bottom margin of the PDF reports are configured in the same wizard and come
from the module `l10n_de_report_footer`.

The paper formats keep 0 mm side margins and disable smart shrinking so that
the CSS millimetres of the layout equal the printed millimetres. When you use
your own paper format with a DIN 5008 layout, keep these settings and set the
top margin equal to the header spacing (27 mm for Form A, 45 mm for Form B).
