Known issues and planned improvements:

- **Official XSD Schema**: The official ELSTER XSD schema files from
  the Anmeldungssteuern ERiC package could be used for automated
  XML validation. Currently, the XML structure follows the
  documented format from the official ELSTER help pages.

- **Steuernummer validation**: Basic format validation only
  (10-13 digits). Full validation against official Finanzamt
  directories could be added.

- **Manual Mein ELSTER import test**: The generated XML conforms
  to the format documented at
  ``https://www.elster.de/eportal/helpGlobal?themaGlobal=ustva_upload``
  but has not yet been tested with an actual Mein ELSTER account.

- **Persistent XML storage**: The generated XML is stored as a
  temporary binary field on the statement. Consider a dedicated
  export history or separate storage approach for audit purposes.
