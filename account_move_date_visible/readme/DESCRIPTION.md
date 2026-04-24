# account_move_date_visible

**Buchungsdatum auf Rechnungen sichtbar schalten (GoB)**

## Zweck

Im Odoo-19-Standard ist das Buchungsdatum (`date`) auf `account.move`
auf Ausgangsrechnungen nur im Quick-Edit-Modus oder bei Abweichung vom
Rechnungsdatum nach Buchung sichtbar. Dieses Modul schaltet das Feld
immer sichtbar, damit die Periodenzuordnung jederzeit nachvollziehbar
ist.

## Regulatorischer Hintergrund

Das Buchungsdatum bestimmt die Periode der FiBu-Buchung und damit die
Umsatzsteuer-Voranmeldung. Bei periodenübergreifenden Fällen (z.B.
Rechnung 05.04. für Leistung 28.03.) wird das Datum im Standard
stillschweigend vom Rechnungsdatum übernommen, was zu einer falschen
Periodenzuordnung führen kann.

**GoB-Grundsatz Zeitgerechtigkeit** (§ 146 AO, GoBD Rz. 45 ff.):
Buchungen müssen der richtigen Periode zugeordnet werden. Das
Buchungsdatum muss daher vom Erfasser sichtbar und kontrollierbar sein.

## Technische Umsetzung

### `views/account_move_views.xml`

View-Erweiterung auf `account.view_move_form`: Das `invisible`-Attribut
von `field[@name='date']` in `group[@id='header_right_group']` wird
auf `0` gesetzt, wodurch das Buchungsdatum unabhängig vom Belegtyp
sichtbar ist.

## Abhängigkeiten

- `account`

## Kompatibilität

- Odoo Community & Enterprise

## Autor

Datenbetrieb GmbH, <https://datenbetrieb.de>

## Lizenz

AGPL-3
