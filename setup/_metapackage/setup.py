import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-germany",
    description="Meta package for oca-l10n-germany Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-datev_export>=16.0dev,<16.1dev',
        'odoo-addon-datev_export_xml>=16.0dev,<16.1dev',
        'odoo-addon-datev_import_csv_dtvf>=16.0dev,<16.1dev',
        'odoo-addon-l10n_de_location_nuts>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
