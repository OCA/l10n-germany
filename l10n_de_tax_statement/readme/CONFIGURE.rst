This module makes use of the tax tags (eg.: 81, 86, 91, 89, 93 ...) as prescribed by the German tax laws and represented by the tax declaration form "Umsatzsteuervoranmeldung".

If the default Odoo German chart of accounts is installed (module l10n_de) you are able to select in the settings if you want to use the skr03 or skr04 chart variant.
By installing and configuring your favored german account chart the tax tags from the module l10n_de are automatically present in the database.

If a non-standard chart of accounts is installed, you have to manually create the tax tags and properly set them into the tax definition. If you create another german account chart (f.e. l10n_de_ikr) you can still depend on l10n_de module in order to benefit from the generic tax tags for germany. If you won't use l10n_de as a base module you have to configure at first your own tax tags. After that, go to go to menu: Invoicing -> Configuration -> Accounting -> German Tax Tags, and manually set the tags in the configuration form; click Apply to confirm (for more information about the installation and configuration of that module, check the README file).
The name of the tags must be formatted this way: "+81 base", "+81 tax", "-81 base", "-81 tax", "+41", "-41", etc...

The user must belong to the *Show Full Accounting Features* group, to be able to access the `Invoicing -> Configuration -> Accounting -> German Tax Tags` menu.
