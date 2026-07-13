All modules toggled from this app's settings page must already be available
in the Odoo `addons_path`.

Clone each repository on the branch matching your Odoo version and add it to
`addons_path` (or install the corresponding `odoo-addon-*` PyPI packages).

## Why these modules are not declared as dependencies

The modules listed in the configuration page are intentionally **not** added to
the `depends` key of this addon. Two reasons:

1. **Opt-in by design.** This addon is a curated catalogue, not a hard bundle.
   A user installing it should be able to pick the workflows they need
   (e.g. SEPA Credit but no DATEV XML, or DATEV without SEPA). Declaring them
   as dependencies would force-install every single module on first install.
2. **Avoid hard coupling to many external repositories.** If any of the listed
   modules is missing, renamed, or unavailable for a given Odoo version,
   installing this addon would fail outright. Keeping them as toggleable
   `module_*` settings means a missing module only affects that one toggle —
   Odoo will simply report it as uninstallable in the UI — instead of blocking
   the whole addon.
