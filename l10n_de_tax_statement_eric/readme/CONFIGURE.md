In Invoicing \> Configuration \> Settings \> ELSTER:

- **ELSTER HerstellerID**: the HerstellerID of the installation, see
  *Installation*.
- **ELSTER Test Transmission**: send the statements with the Testmerker
  700000004. ELSTER deletes them right after their receipt, they aren't
  declared and the statement isn't marked as sent. Use it to test the
  installation and the certificate.
- **Store the ELSTER Certificate**: by default the approval of a
  statement asks for the certificate file (`.pfx`) of Mein ELSTER and
  its PIN, and removes them from the database right after the
  transmission. With this option the file and its PIN are kept on the
  company and the approval sends the statement right away. Only
  administrators can read or replace them. Removing the option deletes
  the stored file and PIN.
- **Datenschutzhinweis der Finanzverwaltung**: the privacy notice of the
  tax administration. The license of ERiC requires every user to read
  it once before sending with it: confirm it here, or the first
  transmission of the user asks for it. Odoo records the date of the
  confirmation on the user and doesn't ask again.

Whoever has the certificate file and its PIN can send declarations in
the name of the company: keep the option off if the database, its
backups or its administrators shouldn't have them.

Only users of the group *Billing Administrator* (Adviser) can send a
statement.
