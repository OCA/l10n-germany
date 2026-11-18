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

The taxes of `l10n_de` in Odoo 18.0 need these corrections:

- **Wrong sign:** these taxes declare the turnover negative. Swap the
  tax grids of the base, `+` on the invoices and `-` on the refunds:
  - *0% EX ND*, tax free without input tax deduction: Kennzahl 48
  - *0% TT F*, first customer of a triangular transaction: Kennzahl 42
  - *0% MOB*, mobile phones and other § 13b UStG supplies: Kennzahl 60
  - *0% EU A*, tax free intra-community acquisitions (vendor bills):
    Kennzahl 91
- **Wrong Kennzahl:**
  - *0% C EXEMPT* is meant for small businesses (§ 19 Abs. 1 UStG) and
    medical services (§ 4 Nr. 14 UStG), which belong to Kennzahl 48. In
    SKR03 it uses Kennzahl 87, in SKR04 it has no tax grid. Set `+48` on
    the base of the invoices and `-48` on the base of the refunds.
  - *19% EU Car* declares its input tax in Kennzahl 59, which is only
    for vehicle suppliers under § 2a UStG. Use `-61` instead of `-59` on
    the invoices and `+61` instead of `+59` on the refunds.
  - *19% CS*, *7% CS* and *19% R MOB*, reverse charge purchases under
    § 13b UStG, declare their base in Kennzahl 84 and in Kennzahl 60.
    Kennzahl 60 is for the supplier only, remove `+60` and `-60` from
    the base.
  - *19% EX D* and *7% EX D*, reverse charge purchases under § 13b
    UStG, declare their input tax in Kennzahl 66. Use `-67` instead of
    `-66` on the invoices and `+67` instead of `+66` on the refunds.
  - *5.5% A* and *10,7% A*, average rates of § 24 UStG, declare every
    sale in Kennzahl 77, which is only for deliveries to customers with
    a VAT ID in other member states. Remove `+77` and `-77` from the
    base, and create a sale tax with 0 % and `+77`/`-77` on the base
    for these deliveries.
- **OSS taxes** (*l10n_eu_oss*, sales to private customers in other
  member states) have no tax grid, so these sales are missing from the
  statement. They belong to Kennzahl 45: set `+45_BASE` on the base of
  the invoices and `-45_BASE` on the base of the refunds of each OSS
  tax.

The accounts of the taxes don't change the statement, but some taxes
book on accounts which DATEV has for other cases, e.g. for an export to
a tax advisor. These taxes book the tax the company owes itself on the
account of Kennzahl 69 for wrongly invoiced tax (§ 14c UStG, SKR03
1783, SKR04 3851), *EX D* also books its input tax on the general input
tax account. Use these accounts instead:

| Tax                   | SKR03       | SKR04       |
|-----------------------|-------------|-------------|
| *19% EX D* input tax  | 1577        | 1407        |
| *19% EX D* output tax | 1787        | 3837        |
| *7% EX D* input tax   | 1578        | 1408        |
| *7% EX D* output tax  | 1785        | 3835        |
| *19% TT F* output tax | 1794        | 3819        |
| *19% OUT*, *7% OUT* output tax | 1769 | 3839 (create it: *Umsatzsteuer aus der Auslagerung von Gegenständen aus einem Umsatzsteuerlager*) |

Changed tax grids only apply to journal items posted afterwards. For an
earlier period, book a manual journal entry in that period which moves
the amounts from the wrong to the right tax grids, and declare it with a
corrected statement.
