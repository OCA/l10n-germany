# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2018 Florian Kantelberg <florian.kantelberg@initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import csv
import requests
import zipfile
from io import BytesIO

COUNTRY_CODE = "DE"


if __name__ == "__main__":
    url = "http://download.geonames.org/export/zip/%s.zip" % COUNTRY_CODE

    print('Downloading from %s' % url)
    response = requests.get(url)
    if response.status_code != requests.codes.ok:
        print('Error while downloading: %s.' % response.status_code)
        exit(response.status_code)

    print('Decompressing archive...')
    zipped = zipfile.ZipFile(BytesIO(response.content), 'r')
    data = zipped.read('%s.txt' % COUNTRY_CODE).decode('UTF-8').splitlines()

    dialect = csv.excel
    dialect.delimiter = "\t"
    reader = csv.reader(data, dialect=dialect)

    print('Generate the XML...')
    output = open("l10n_de_toponyms_zipcodes.xml", 'w')
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<odoo noupdate="1">\n')
    for k, row in enumerate(reader):
        zipcode, city, _, state_code = row[1: 5]
        state = "l10n_de_country_states.res_country_state_%s" % state_code
        city_id = "city_DE_%s" % k
        lat, lon = row[9: 11]

        output.write(''.join([
            ' ' * 8 + '<record id="%s" model="res.better.zip">\n' % city_id,
            ' ' * 12 + '<field name="state_id" ref="%s"/>\n' % state,
            ' ' * 12 + '<field name="city">%s</field>\n' % city,
            ' ' * 12 + '<field name="name">%s</field>\n' % zipcode,
            ' ' * 12 + '<field name="country_id" ref="base.de"/>\n',
            ' ' * 12 + '<field name="latitude">%s</field>\n' % lat,
            ' ' * 12 + '<field name="longitude">%s</field>\n' % lon,
            ' ' * 8 + '</record>\n',
        ]))

    output.write('</odoo>\n')
    output.close()
    print("Done.")
