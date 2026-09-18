## L10n DIN5008 Report Margin Bottom

This module extends the DIN 5008 report layout with a configurable bottom page margin.

The default DIN 5008 bottom margin may not provide enough space when the report footer contains
additional or customized content. This can occur, for example, when extending the standard footer with
additional company information or modules such as company representatives. Depending on the amount of
content, the footer may require more vertical space than the standard configuration allows.

Features:
* Configure the bottom page margin for DIN 5008 PDF reports in millimeters.
* Restrict the configured bottom margin to a valid range of 5 to 60 mm.
* Manage the bottom margin in the company document layout configuration.
* Apply the configured margin to reports using the DIN 5008 external report layout.
* Pass the configured margin to wkhtmltopdf when generating DIN 5008 PDF reports.
* Preserve existing report-specific paperformat arguments when applying the DIN 5008 margin.

The setting is available in the company document layout configuration and applies to reports using the
DIN 5008 external report layout.
