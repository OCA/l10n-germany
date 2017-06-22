.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

==========================
Steuernummer VAT validator
==========================

This module was written to extend the functionality of base_vat to support
validation of german SteuerNummer following this schema:
https://de.wikipedia.org/wiki/Steuernummer


Usage
=====

#. Go to Contacts.
#. Create a new record.
#. Put a SteuerNummer in the VAT field preceded by 'DE'.
#. It won't fail.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/175/10.0

Known issues / Roadmap
======================

* This validator only checks that number is 10 or 11 digit length. Validation
  depends on Tax Office that generates the SteuerNummer.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-germany/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and
welcomed feedback `here <https://github.com/OCA/l10n-germany/issues/new>`_.

Credits
=======

Contributors
------------

* Rafael Blasco <rafael.blasco@tecnativa.com>
* Antonio Espinosa
* Pedro M. Baeza <pedro.baeza@tecnativa.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
