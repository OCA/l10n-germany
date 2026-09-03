# Usage

This module helps comply with the German §35a EStG tax deduction requirements for household-related labor services.

## Creating Invoices with Labor Costs

1. Go to **Invoicing** → **Customers** → **Invoices**
2. Create a new customer invoice
3. Add invoice lines using products marked as "Is Labor Cost Product"
4. The module automatically:
   - Calculates the net labor cost amount
   - Calculates the VAT amount
   - Calculates the gross labor cost amount
5. When the invoice is confirmed, the labor cost disclosure notice appears automatically

## Viewing Labor Cost Values

On confirmed invoices, you can see the calculated labor cost values in the invoice form:

- **Labor Cost (Net)**: Total net amount from labor cost product lines
- **Labor Cost (Tax)**: Total VAT amount from labor cost product lines  
- **Labor Cost (Gross)**: Total gross amount (net + tax)

These fields are computed automatically and cannot be edited manually.

## Invoice Output

When printing or sharing an invoice that contains labor cost products, a disclosure notice is automatically appended showing:

- Total invoice amount
- Labor costs (gross) included
- Labor costs (net) included
- VAT included

This satisfies the §35a EStG documentation requirements for tax deduction claims.