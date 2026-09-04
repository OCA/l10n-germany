**Always show the accounting date on invoices**

## Purpose

In the Odoo standard, the accounting date (`date`) on `account.move` is
only shown on customer invoices in quick-edit mode, or after posting if
it differs from the invoice date. This module makes the field visible at
all times, so that the period a document is booked into is always
apparent to the person entering it.

## Why it matters

The accounting date determines the period of the ledger entry, and with
it the period of the VAT return. In cases that straddle a period
boundary — an invoice dated 5 April for a service delivered 28 March —
the standard silently derives the accounting date from the invoice date,
which can book the entry into the wrong period. Making the field visible
turns that into a deliberate, checkable decision instead of a hidden
default.

Many jurisdictions require exactly this. In Germany, for instance, the
principle of timeliness (*Grundsatz der Zeitgerechtigkeit*, § 146 AO and
GoBD margin no. 45 ff.) obliges entries to be assigned to the correct
period, which presupposes that the person recording them can see and
control the accounting date.

## Implementation

`views/account_move_views.xml` extends `account.view_move_form` and sets
the `invisible` attribute of `field[@name='date']` inside
`group[@id='header_right_group']` to `0`, making the accounting date
visible regardless of the document type or state.

## Dependencies

- `account`

## Compatibility

Odoo Community and Enterprise.
