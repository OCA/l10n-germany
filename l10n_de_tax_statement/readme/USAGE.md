To create a statement:

1.  Go to Invoicing \> Reporting \> German VAT Statement
2.  Create a statement and choose the year and the period, a month or a
    quarter, like in the ELSTER form. A period has one statement, any
    further statement of the period is a *Corrected Statement*.
3.  The statement computes its Kennzahlen from the posted journal items
    dated in the period when it is created. Kennzahl 83, the remaining
    advance payment, is computed from them. Check the lines: the amounts
    can't be changed by hand, correct the journal items, or book a
    manual journal entry with the tax grid of the Kennzahl, e.g. `39`,
    and press *Update* to compute them again.
4.  Press *Approve* once the lines are right. The approval computes the
    lines again and stops if they changed since you checked them, e.g.
    because of journal items posted meanwhile.
5.  The approved statement is final and counts as declared. The approval
    attaches it as ELSTER XML: upload it in Mein ELSTER into the form of
    the Umsatzsteuer-Voranmeldung. It declares the tax bases in full
    euros, rounded half up. The XML needs the tax number, the federal
    state and the address of the company, and the ELSTER HerstellerID in
    Invoicing \> Configuration \> Settings. Enter the W-IdNr. of the
    company as issued, e.g. `DE123456789-00001`: the XML declares it
    without the suffix, as ELSTER only takes `DE` and the nine digits.
    The W-IdNr. is optional, without it the XML leaves it out.
6.  An approved statement can't be changed or reset, correct it with a
    corrected statement of the period. Its approval refers to the last
    approved statement of the period in *Corrects*, empty if the period
    was declared outside of Odoo.

Journal items posted later into a period you already declared are not
part of any other statement, declare them with a corrected statement of
that period.
