To configure this module, you need to:

#. Go to your company
#. Fill in the fields in the `DATEV` tab
#. For accounts where you want to suppress automatic calculations (for ie taxes), set the according flag

The module also contains an inactive cronjob and a mail template allowing you to send period DATEV export somewhere via email. It relies on finding exactly one date range for the previous month and one for the year of the previous month, otherwise you'll see an error message in your log when running the cronjob. Note that the data transmitted via email is not encrypted.
