## L10n DIN5008 Report Footer Representative

This glue module integrates representatives from the `res_company_representative` to the DIN 5008
report layout footer legal section

Features:
* Optionally display company representatives in the Legal Notes section of DIN 5008 reports.
* Display company representatives before the VAT identification number and other legal company information.
* Display the representative's role alongside their name.
* Support multiple representatives with identical or different roles.
* If a single representative is configured, their role and name are displayed together.
* If multiple representatives have the same role, the role is displayed once, followed by the representatives' names.
* If representatives have different roles, the first line is labeled "Representatives", followed by each representative's name and their respective role.
* Manage and preview the configured representatives in the company document layout configuration.

The settings are available in the company document layout configuration and apply to reports using the DIN 5008 external report layout.
