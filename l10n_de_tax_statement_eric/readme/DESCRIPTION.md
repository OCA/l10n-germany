This module sends the German VAT Statement (Umsatzsteuer-Voranmeldung)
of *l10n_de_tax_statement* to ELSTER with ERiC, the ELSTER Rich Client
library of the tax administration, instead of the upload of the XML
export in Mein ELSTER.

It validates the statement with ERiC and sends it on its approval with
the ELSTER certificate of the company and posts the transfer ticket and
the transmission protocol of ELSTER in the chatter.

ERiC isn't part of this module: its license doesn't allow to pass it on,
see *Installation*.
