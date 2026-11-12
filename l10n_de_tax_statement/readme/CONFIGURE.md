The statement takes its amounts from the tax grids (tax tags) of the
German localization, which are named after the Kennzahlen of the form,
e.g. `81_BASE`, `81_TAX`, `66`. A journal item ends up in a Kennzahl
only through its tax grids:

- **Invoices and bills:** the taxes set the tax grids on the journal
  items when they are posted. Check the tax grids of a tax in Invoicing
  \> Configuration \> Taxes, tab *Definition*, column *Tax Grids*. A tax
  without tax grids is missing on the statement.
- **Manual journal entries:** use a tax on the line, or set the tax grid
  of the Kennzahl on the journal item itself, e.g. `62` for the import
  VAT paid. An amount booked straight on a tax account without a tax
  grid is missing on the statement.
- **Payments and the transfer of the tax to the tax office** carry no
  tax grids and aren't part of the statement.
- **Kennzahlen without a tax:** no standard tax uses Kennzahl 37, 39,
  49, 50, 59, 63, 64, 65, 73/74, 87, 90 and 95/98, only inactive taxes
  use 35/36 (*x%*), 62 (*19% EX*, *7% EX*) and 76/80 (*19% A*). Book
  them with a manual journal entry with the tax grid of the Kennzahl,
  activate the tax, or create a tax with the tax grids of the Kennzahl
  (see below for 73/74 and 87).

A tax grid which isn't named after a Kennzahl, e.g. a renamed or a
custom one, has no row on the statement. *Update* lists its amount in
the section *Steuer-Tags ohne Kennzahl (nicht gemeldet)* at the end,
which isn't declared to ELSTER. Use the tax grid of the Kennzahl
instead.

The sign of a tax grid tells how the amount adds up: on an invoice, the
base of a turnover needs the `+` grid, on a refund the `-` grid. Use
the magnifier buttons of a statement line to see the journal items of a
Kennzahl.

These Kennzahlen need a tax of their own:

- **Kennzahl 87** (0 % tax rate, § 12 Abs. 3 UStG, e.g. solar panels for
  private customers): no tax fits. Create a sale tax with 0 %, tax grid
  `+87` on the base of the invoices and `-87` on the base of the
  refunds.
- **Kennzahl 73 and 74** (§ 13b Abs. 2 Nr. 2 and 3 UStG, e.g. the
  realization of goods transferred as security, or a property sale
  taxed by option): no tax fits. Book them with a manual journal entry
  with the tax grids of the Kennzahlen, or create a purchase tax like
  *19% CS* with `+73` on the base, a tax line of 100 % with `-67` (input
  tax) and one of -100 % with `-74` (tax due) on the vendor bills, and
  the opposite grids on the refunds.
