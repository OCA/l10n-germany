.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================
German Tax Statement
=========================

This module provides the Tax Statement in German format. Based on that report you will get all the values you need to enter in the portal elsteronline.de to declare easily your german VAT's by reading the values from the VAT statement report which is a clone of the official VAT statement formular. The accountant or tax/accounting advisor being responsible to declare the taxes just need to search for the right line in the VAT statement report in order to transmit those value into the elsteronline.de formular. Some of the base values have to be entered as a integer value without exact decimal values. The official elsteronline.de website portal will inform you about the relevant value formattings to guide you through the process of entering, confirming and sending your periodical (i.e. monthly) german VAT tax declarations.

Installation
============

* This module depends from module account_tax_balance available at https://github.com/OCA/account-financial-reporting.

Configuration
=============

This module depends on the tax tags (eg.: 81, 86, 89, 91, 61...) as prescribed by the german tax laws.

If the default Odoo German chart of accounts is installed (module l10n_de) then these tags are automatically present in the database. If this is the case, go to menu: Invoicing -> Configuration -> Accounting -> German Tax Tags, and check that the tags are correctly set; click Apply to confirm.

If a non-standard chart of accounts is installed, you have to manually create the tax tags and properly set them into the tax definition. After that, go to go to menu: Invoicing -> Configuration -> Accounting -> German Tax Tags, and manually set the tags in the configuration form; click Apply to confirm, in order to use that form to be populated by the relevant invoice taxes from the choosen tax period.


Usage
=====

#. Verify that you have enough permits. You need to belong at least to the Accountant group.
#. Go to the menu: Invoicing -> Reports > Taxes Balance > DE Tax Statement
#. Create a statement, provide a name and specify start date and end date
#. Press the Update button to (re-) calculate the report: the report lines will be displayed in the tab Statement
#. Eventually you have to manually enter the Tax amounts of lines in Edit mode, click on the amount of the line to be able to change the values (f.e. to remove decimal values) .
#. Press the Post button to set the status of the statement to Posted; the statements set to this state cannot be modified anymore
#. If you need to recalculate or modify or delete a statement already set to Posted status you need first to set it back to Draft status: press the button Reset to Draft
#. If you need to print the report in PDF, open a statement form and click: Print -> DE Tax Statement
#. On the second tab of the statement you have the possibility to add undeclared invoices from the past to the VAT statement. By pressing the "Update" button you will add the in the statement's report.



Known issues / Roadmap
======================

* Exporting formats not yet available
* If you have used the V10 version of that module, it might need some adoptions as the tax lines of the statement report was revised for the V11 module.
* If the usual german tax rates would become more expensive or even cheaper as 19% and 7% the module would need some refactoring, in order to reflect those tax adoptions in order to calculate proper values. Eventually we can improve the module by fetching the tax values from some taxes instead of calculting these values in order to prepare the tax fields of this report. However to do that we need to assign for each tax in the german account plan (modules l10n_de_skr03 and l10n_de_skr04) a tax tag for the base amount as well also the tax tag for the tax value, which is currently not the case. Currently we have assigned to many taxes in the mentioned localisation modules just one tax tag. Nevertheless the tax calculation in this module should not differ from the values, if we would fetch them by tax tags for the tax amount.
* Maybe we could add more german specific tax cases inside the "test" directory.



Credits
=======

Contributors
------------
* Thorsten Vocks <thorsten.vocks@openbig.org>
* Andrea Stirpe <a.stirpe@onestein.nl>
* Antonio Esposito <a.esposito@onestein.nl>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is not yet maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org or the corresponding github repository. 
