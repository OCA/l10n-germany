After installation, you must click at import wizard to populate NUTS items
in Odoo database in:
Contacts > Configuration  > Import NUTS 2024

This wizard will download from Europe ShowVoc service the metadata to
build NUTS in Odoo. Each localization addon (l10n_es_location_nuts,
l10n_de_location_nuts, ...) will inherit this wizard and
relate each NUTS item with states. So if you install a new localization addon
you must re-build NUTS clicking this wizard again.
