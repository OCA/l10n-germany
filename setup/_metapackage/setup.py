import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-germany",
    description="Meta package for oca-l10n-germany Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-datev_export',
        'odoo14-addon-datev_export_xml',
        'odoo14-addon-l10n_de_country_states',
        'odoo14-addon-l10n_de_holidays',
        'odoo14-addon-l10n_de_location_nuts',
        'odoo14-addon-l10n_de_skr03_mis_reports',
        'odoo14-addon-l10n_de_skr04_mis_reports',
        'odoo14-addon-l10n_de_steuernummer',
        'odoo14-addon-l10n_de_tax_statement',
        'odoo14-addon-l10n_de_tax_statement_zm',
        'odoo14-addon-l10n_de_toponyms',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
