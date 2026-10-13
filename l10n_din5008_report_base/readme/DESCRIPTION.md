## L10n DIN5008 Report Base
This module provides the base functionality for configuring and extending DIN 5008 report layouts in Odoo.
It introduces a centralized configuration dialog with a live report preview, allowing users to configure DIN 5008 layout settings and identify the corresponding report elements directly in the preview. A registry mechanism allows additional modules to contribute their own configuration fields without modifying the base configuration dialog.

### Features
* Configure DIN 5008 report settings through the company document layout.
* Display a live report preview in the configuration dialog.
* Highlight corresponding report elements in the preview when selecting configuration fields.
* Store all DIN 5008 settings in a centralized JSON field on the company.
* Reset the configuration to its default values.
* Store only values that differ from the default configuration.
* Automatically apply default values for settings that have not been explicitly overridden.
* Configure fold marks and punch/hole marks.
* Configure company logo position, margins, and size, with different default sizes for DIN 5008 Type A and Type B.
* Customize sender address formatting, including separators and spacing.
* Configure country indicators for sender addresses.
* Adjust sender and recipient address font scaling independently.
* Separate sender and recipient address styling in DIN 5008 reports.
* Configure the sender address left margin.
* Configure the bottom page margin.
* Support reusable configuration fields, including booleans, selections, numeric values, text, and lists.
* Validate configuration values before applying changes.
* Allow additional modules to register their own DIN 5008 settings without modifying the base configuration dialog.
* Apply configured settings to DIN 5008 reports.


The configuration is stored in a single JSON field on the company, which serves as the central source of truth for DIN 5008 settings.
Default values are generated from the registered configuration fields. Only settings that differ from their defaults are stored as overrides. This keeps the stored configuration compact and allows default values to evolve with the module.

Users can reset the configuration to its default values. Resetting clears the stored overrides, allowing the default configuration to take effect again.

Additional modules can extend the configuration through the registry mechanism. They can register module-specific settings, define their types and default values, and specify preview selectors for highlighting corresponding report elements.
This approach keeps module-specific settings separate while reusing the base configuration dialog, preview functionality, and centralized storage.
