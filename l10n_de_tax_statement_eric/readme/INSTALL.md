ERiC is a native library of the tax administration. Its license only
grants the use to the software manufacturer who downloaded it and
doesn't allow to pass it on, so neither this module nor its repository
contain it. Every operator gets it from ELSTER:

1.  Register as software developer in the ELSTER developer area
    (<https://www.elster.de/elsterweb/entwickler>) and apply for a
    HerstellerID. ELSTER requires it in every transmission, enter it in
    Invoicing \> Configuration \> Settings \> ELSTER.
2.  Download the ERiC package for the platform of the Odoo server, e.g.
    `ERiC-44.3.6.0-Linux-x86_64.jar`, from the download area for
    developers and accept its license. This module needs ERiC 44 or
    newer, on Linux with glibc 2.28 or newer. The version must support
    the Datenartversion of the statement, e.g. `UStVA_2026`, see
    *Datenartversionmatrix.ods* of the ERiC documentation.
3.  Extract it on the Odoo server, the package is a zip archive:
    `unzip ERiC-44.3.6.0-Linux-x86_64.jar -d /opt`. Keep the library
    and its `plugins` directory together, ERiC searches its plugins next
    to `libericapi.so`.
4.  Point the Odoo server to the library in its configuration file:

    ``` ini
    [options]
    l10n_de_eric_library = /opt/ERiC-44.3.6.0/Linux-x86_64/lib/libericapi.so
    ; optional, the directory of eric.log, by default the temporary directory
    l10n_de_eric_log_path = /var/log/odoo/eric
    ```

    The environment variables `L10N_DE_ERIC_LIBRARY` and
    `L10N_DE_ERIC_LOG_PATH` work as well. The path is a server setting
    on purpose: the library runs inside the Odoo process, so it can't be
    set from the database.

5.  Restart Odoo and install this module.

ELSTER publishes new ERiC versions regularly and the license requires to
use a current one: replace the library and update the path when a new
version is out.
