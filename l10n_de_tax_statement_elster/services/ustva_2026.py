# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""UStVA 2026 constants for ELSTER export."""

NAMESPACE_USTVA = "http://finkonsens.de/elster/elsteranmeldung/ustva/v2026"
SCHEMA_VERSION = "2026"
TAX_YEAR = "2026"


def get_xml_schema_version():
    """Return the ELSTER XML schema version for UStVA 2026.

    The schema version '2026' is required for the restructured
    2026 tax form. ELSTER rejects older schema versions.

    Source: https://www.elster.de/eportal/helpGlobal?themaGlobal=ustva_upload
    """
    return SCHEMA_VERSION


def get_namespace():
    """Return the ELSTER UStVA upload namespace."""
    return NAMESPACE_USTVA
