import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-l10n-germany",
    description="Meta package for oca-l10n-germany Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-datev_export',
        'odoo13-addon-datev_export_xml',
        'odoo13-addon-l10n_de_country_states',
        'odoo13-addon-l10n_de_holidays',
        'odoo13-addon-l10n_de_skr03_mis_reports',
        'odoo13-addon-l10n_de_skr04_mis_reports',
        'odoo13-addon-l10n_de_tax_statement',
        'odoo13-addon-l10n_de_toponyms',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
