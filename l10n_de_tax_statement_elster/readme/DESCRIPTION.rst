This module adds ELSTER XML export for the German VAT Statement
(Umsatzsteuervoranmeldung).

The generated XML file can be imported into Mein ELSTER using the
"Formulardaten hochladen" function, avoiding manual data entry.

**Currently supported:**
- Tax form version 2026 (Steuerjahr 2026)
- All 16 valid UStVA periods (12 months + 4 quarters)
- Anmeldungssteuern XML format (namespace ``v2026``, ``ISO-8859-15``)
- 43 Kennzahlen exported as Kz* elements
- Tax bases in full euros, tax amounts in comma-decimal format

**Not included:**
- Direct ERiC/ELSTER server transmission
- Certificate management
- Automatic submission
- Annual tax return (Jahreserklärung)
- Zusammenfassende Meldung (ZM)
