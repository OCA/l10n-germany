# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models

from .layout_din5008_mixin import (
    DIN5008_ADDRESS_HEIGHT,
    DIN5008_INFO_LEFT,
    DIN5008_INFO_WIDTH,
    DIN5008_LAYOUT_KEYS,
    DIN5008_REMARK_ZONE_HEIGHT,
)

# prefix of the keys of the DIN 5008 settings in report_layout_config
DIN5008_CONFIG_PREFIX = "din5008."


class ReportLayoutConfigMixin(models.AbstractModel):
    _inherit = "report.layout.config.mixin"

    def _get_din5008_geometry_section(self):
        """Section (tab of the wizard) holding the positions of the DIN 5008 layouts."""
        return {
            "section": "din5008_geometry",
            "section_label": self.env._("Positions (mm)"),
            "section_sequence": 30,
        }

    @api.model
    def get_report_layout_config_fields(self, layout_key=None):
        """Offer the bottom margin in the tab "Positions (mm)" of the DIN layouts.

        The base module declares the bottom margin in its own tab *Page*. For
        the DIN 5008 layouts the setting is moved to the end of the positions
        tab, next to the other distances in mm; other layouts are not affected.
        """
        specs = super().get_report_layout_config_fields(layout_key)
        if layout_key not in DIN5008_LAYOUT_KEYS:
            return specs
        margin = [spec for spec in specs if spec["key"] == "page.margin_bottom"]
        if not margin:
            return specs
        return [spec for spec in specs if spec["key"] != "page.margin_bottom"] + [
            {
                **margin[0],
                **self._get_din5008_geometry_section(),
                "label": self.env._("Bottom Margin"),
            }
        ]

    def _get_report_layout_config_fields(self):
        """Settings of the DIN 5008 layouts, offered for these layouts only."""
        layouts = list(DIN5008_LAYOUT_KEYS)
        document = {
            "section": "din5008_document",
            "section_label": self.env._("DIN 5008 Document"),
            "section_sequence": 10,
            "layouts": layouts,
        }
        sender = {
            "section": "din5008_sender",
            "section_label": self.env._("Sender Line"),
            "section_sequence": 20,
            "layouts": layouts,
        }
        geometry = {**self._get_din5008_geometry_section(), "layouts": layouts}
        sender_line_on = {"visible_if": {"din5008.sender_line": True}}
        return super()._get_report_layout_config_fields() + [
            {
                **document,
                "key": "din5008.informations_position",
                "label": self.env._("Document Information"),
                "help": self.env._(
                    "Where the document information (dates, references, ...) of "
                    "the standard reports is printed. 'Beside the address' moves "
                    "the block next to the address window after rendering."
                ),
                "type": "selection",
                "default": "beside",
                "options": [
                    ("below", self.env._("Below the title (standard position)")),
                    (
                        "beside",
                        self.env._("Beside the address (DIN 5008 information block)"),
                    ),
                ],
            },
            {
                **document,
                "key": "din5008.logo_position",
                "label": self.env._("Logo Position"),
                "help": self.env._(
                    "Horizontal position of the company logo in the letterhead. "
                    "The tagline is printed on the opposite side."
                ),
                "type": "selection",
                "default": "left",
                "options": [
                    ("left", self.env._("Left")),
                    ("right", self.env._("Right")),
                ],
            },
            {
                **document,
                "key": "din5008.fold_marks",
                "label": self.env._("Fold Marks"),
                "help": self.env._(
                    "Print the fold marks on the left edge of every page."
                ),
                "type": "boolean",
                "default": False,
            },
            {
                **document,
                "key": "din5008.hole_mark",
                "label": self.env._("Hole Mark"),
                "help": self.env._(
                    "Print the hole mark on the left edge of every page."
                ),
                "type": "boolean",
                "default": False,
            },
            {
                **sender,
                "key": "din5008.sender_line",
                "label": self.env._("Print Sender Line"),
                "help": self.env._(
                    "Print the company address as a single line above the "
                    "recipient address (Rücksendeangabe), visible in the "
                    "envelope window."
                ),
                "type": "boolean",
                "default": True,
            },
            {
                **sender,
                **sender_line_on,
                "key": "din5008.sender_separator",
                "label": self.env._("Separator"),
                "help": self.env._(
                    "Character between the lines of the address printed as "
                    "sender line above the recipient. The company name and "
                    "address formatted this way are available as the placeholder "
                    "'DIN 5008 Sender Line Text' in the address, tagline and "
                    "footer texts of the document layout."
                ),
                "type": "selection",
                "default": "pipe",
                "options": [
                    ("pipe", self.env._("Pipe (|)")),
                    ("bullet", self.env._("Bullet (•)")),
                    ("middot", self.env._("Middle dot (·)")),
                ],
            },
            {
                **sender,
                **sender_line_on,
                "key": "din5008.sender_country",
                "label": self.env._("Country"),
                "help": self.env._(
                    "How the country of the company is printed in the placeholder "
                    "'DIN 5008 Sender Line Text' (insert it into the address of "
                    "the document layout to print it as sender line)."
                ),
                "type": "selection",
                "default": "none",
                "options": [
                    ("none", self.env._("No country")),
                    ("code", self.env._("Country code before the postal code")),
                    ("name", self.env._("Country name")),
                ],
            },
            {
                **geometry,
                "key": "din5008.address_offset_top",
                "label": self.env._("Address Window Offset"),
                "help": self.env._(
                    "Vertical shift of the address window relative to the DIN 5008 "
                    "position directly below the letterhead. Negative values move "
                    "it up."
                ),
                "type": "integer",
                "default": 0,
                "min": -10,
                "max": 30,
                "step": 1,
                "highlight": "address",
            },
            {
                **geometry,
                "key": "din5008.address_height",
                "label": self.env._("Address Window Height"),
                "help": self.env._(
                    "Minimum height of the address window row. The document title "
                    "starts below this row."
                ),
                "type": "integer",
                "default": DIN5008_ADDRESS_HEIGHT,
                "min": 20,
                "max": 80,
                "step": 1,
                "highlight": "address",
            },
            {
                **geometry,
                "key": "din5008.remark_zone_height",
                "label": self.env._("Remark Zone Height"),
                "help": self.env._(
                    "Height of the remark zone (Zusatz- und Vermerkzone) between "
                    "the sender line and the recipient address. DIN 5008 reserves "
                    "%s mm; 0 places the recipient address directly below the "
                    "sender line.",
                    DIN5008_REMARK_ZONE_HEIGHT,
                ),
                "type": "float",
                "default": 0,
                "min": 0,
                "max": 20,
                "step": 0.1,
                "highlight": "address",
            },
            {
                **geometry,
                "key": "din5008.info_left",
                "label": self.env._("Information Block Left"),
                "help": self.env._(
                    "Distance of the information block from the left edge of the page."
                ),
                "type": "integer",
                "default": DIN5008_INFO_LEFT,
                "min": 105,
                "max": 160,
                "step": 1,
                "highlight": "information_block",
            },
            {
                **geometry,
                "key": "din5008.info_width",
                "label": self.env._("Information Block Width"),
                "help": self.env._(
                    "Width of the information block next to the address window."
                ),
                "type": "integer",
                "default": DIN5008_INFO_WIDTH,
                "min": 30,
                "max": 90,
                "step": 1,
                "highlight": "information_block",
            },
        ]
