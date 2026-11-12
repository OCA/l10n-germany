1.  Create the statement and check its lines as described in *German
    VAT Statement*.
2.  Press *Approve*: with this module the approval sends the statement
    to ELSTER. ERiC validates it against the rules of ELSTER first,
    errors stop the approval before anything is sent. With the
    certificate and its PIN stored on the company it sends it right
    away. Otherwise it asks for them: upload the certificate file of
    Mein ELSTER, enter its PIN and press *Send*, which approves the
    statement with them. The first transmission of a user also asks to
    read the privacy notice of the tax administration, once. Without
    ERiC configured on the server, *Approve* attaches the XML for the
    upload in Mein ELSTER like without this module.
3.  ELSTER returns a transfer ticket and the transmission protocol: the
    statement is *Approved* and its message in the chatter has the
    ticket, the notes of ERiC and ELSTER and the protocol. Errors of
    ERiC or ELSTER are shown and the statement stays a draft. A test
    transmission leaves it a draft as well.
