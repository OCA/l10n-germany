# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree


def add_element(namespace, parent, tag, text=None, **attrib):
    """Add the element ``tag`` of ``namespace`` with ``text`` and ``attrib``
    to ``parent`` and return it"""
    element = etree.SubElement(parent, f"{{{namespace}}}{tag}", attrib)
    if text is not None:
        element.text = text
    return element
