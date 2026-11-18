## 18.0.4.0.0

- The statement follows the ELSTER form: it has a year and a period, a
  month or a quarter, and its lines are the rows of the form with their
  Kennzahlen. It exports the ELSTER XML for the upload in Mein ELSTER.
- The migration converts the date range of a statement to its year and
  period. A date range which is neither a month nor a quarter gets the
  month of its start date and a note to check it. A further statement
  of the same period becomes a corrected statement. The migration
  doesn't convert the lines, as they follow the line numbers of the old
  forms. It keeps them as a message on the statement, press *Update* on
  a draft statement to compute them again.
- The PDF report is removed: check the statement in its form, ELSTER
  provides the transmission protocol.
