{
    "name": "German VAT Statement ELSTER Export",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-germany",
    "depends": ["l10n_de_tax_statement"],
    "external_dependencies": {"python": ["lxml"]},
    "data": [
        "views/l10n_de_tax_statement_views.xml",
    ],
    "installable": True,
}
