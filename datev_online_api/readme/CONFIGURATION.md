Before configuring the API in Odoo you must go to the DATEV portal and create a new App.
It is recommended to use `OpenID Connect Authorization Code Flow` as
**Authorization Flow** and `Confidential` as **Client Type** to allow long term tokens.
Depending on the module selection you need different products to subscribe to. At minimum
`accounting:clients` is recommended.

Go to the **Invoicing \> Configuration** and the following data in the DATEV section:

1. Client Number
2. Consultant Number
3. Client ID and Secret from the DATEV Portal App Credentials
