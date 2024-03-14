import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-germany",
    description="Meta package for oca-l10n-germany Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-datev_export>=15.0dev,<15.1dev',
        'odoo-addon-datev_export_xml>=15.0dev,<15.1dev',
        'odoo-addon-l10n_de_holidays>=15.0dev,<15.1dev',
        'odoo-addon-l10n_de_skr04_mis_reports>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
