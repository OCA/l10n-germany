# Germany - Invoice Labor Cost Disclosure (§35a EStG)

This module extends Odoo's German localization to support the labor cost disclosure requirement according to §35a EStG (German Income Tax Act).

## Overview

German tax law (§35a EStG) allows taxpayers to claim a tax deduction for certain household-related labor services. To qualify, invoices must separately disclose the labor cost portion (net amount), the applicable VAT, and the total gross amount.

This module automatically calculates and displays these values on invoices for products marked as "labor cost products".

## Features

### 1. Labor Cost Product Flag
- New boolean field `Is Labor Cost Product` on product templates
- Products can be marked as labor cost products to enable automatic calculation
- Constraint prevents products of type "Goods" or "Combo" from being marked as labor cost products

### 2. Automatic Calculation
- Computes three monetary fields on invoices:
  - **Labor Cost (Net)**: Sum of net amounts from labor cost product lines
  - **Labor Cost (Tax)**: Sum of VAT amounts from labor cost product lines
  - **Labor Cost (Gross)**: Total gross amount (net + tax)

### 3. Invoice Disclosure
- Displays a formatted notice on invoices when labor costs are present
- Shows the total invoice amount, labor cost breakdown including:
  - Gross labor costs
  - Net labor costs (labor)
  - Included VAT

## Technical Details

- **Module Name**: `l10n_de_invoice_labor_cost`
- **Category**: Localization/Germany
- **License**: AGPL-3
- **Version**: 18.0.1.0.0
- **Dependencies**: `account`

## See Also

- [§35a EStG - German Income Tax Act](https://www.gesetze-im-internet.de/estg/__35a.html)
- [Overview of favored services] https://esth.bundesfinanzministerium.de/esth/2021/C-Anhaenge/Anhang-27b/II/anlage-1.pdf?__blob=publicationFile&v=2