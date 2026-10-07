import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

const din5008ConfigRegistry = registry.category("din5008_config_fields");

din5008ConfigRegistry.add("footer_line_height", {
    key: "footer.line_height",
    label: _t("Line Height"),
    section: "footer",
    sectionLabel: _t("Footer"),
    sectionPriority: 90,
    type: "float",
    default: 1.3,
    min: 0.5,
    max: 4.0,
    step: 0.1,
    previewSelector: ".footer table.table-borderless",
});

din5008ConfigRegistry.add("footer_separator_spacing", {
    key: "footer.separator_spacing",
    label: _t("Spacing to Separator Line"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "float",
    default: 0.0,
    min: 0,
    max: 5,
    step: 0.25,
    previewSelector: ".footer table.table-borderless",
});

din5008ConfigRegistry.add("footer_font_scale_factor", {
    key: "footer.font_scale_factor",
    label: _t("Font Scale Factor"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "float",
    default: 1.0,
    min: 0.75,
    max: 2.0,
    step: 0.05,
    previewSelector: ".footer table.table-borderless",
});

din5008ConfigRegistry.add("footer_fa_contact_preset", {
    key: "footer.fa_contact_preset",
    label: _t("Font Awesome Contact Preset"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "boolean",
    default: false,
    previewSelector: ".footer table.table-borderless tr > td:nth-child(2)",
});

din5008ConfigRegistry.add("footer_bank_acc_holder", {
    key: "footer.bank_acc_holder",
    label: _t("Show Bank Account Holder"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "boolean",
    default: false,
    previewSelector: ".footer table.table-borderless tr > td:nth-child(4)",
});
din5008ConfigRegistry.add("footer_bank_acc_limit1", {
    key: "footer.footer_bank_acc_limit1",
    label: _t("Show only one Bank Account"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "boolean",
    default: false,
    previewSelector: ".footer table.table-borderless tr > td:nth-child(4)",
});
din5008ConfigRegistry.add("footer_table_width_pattern", {
    key: "footer.table_width_pattern",
    label: _t("Footer Table Width Pattern"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "text",
    default: "25,25,25,25",
    previewSelector: ".footer table.table-borderless",

    validate(value) {
        const values = String(value)
            .split(",")
            .map((item) => Number.parseFloat(item.trim()));

        return (
            values.length === 4 &&
            values.every((item) => Number.isFinite(item) && item > 0) &&
            Math.abs(values.reduce((sum, item) => sum + item, 0) - 100) < 0.001
        );
    },

    validationError: _t(
        "The footer table width pattern must contain exactly four positive values whose sum is 100."
    ),
});

din5008ConfigRegistry.add("footer_show_vat", {
    key: "footer.show_vat",
    label: _t("Show VAT-ID"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "boolean",
    default: true,
    previewSelector: ".footer table.table-borderless tr > td:nth-child(3)",
});

din5008ConfigRegistry.add("footer_show_company_registry", {
    key: "footer.show_company_registry",
    label: _t("Show Registry Number"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "boolean",
    default: true,
    previewSelector: ".footer table.table-borderless tr > td:nth-child(3)",
});

din5008ConfigRegistry.add("footer_show_de_tax_number", {
    key: "footer.show_de_tax_number",
    label: _t("Show Tax Number"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "boolean",
    default: false,
    previewSelector: ".footer table.table-borderless tr > td:nth-child(3)",
});

din5008ConfigRegistry.add("footer_show_de_widnr", {
    key: "footer.show_de_widnr",
    label: _t("Show W-Id. No."),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "boolean",
    default: false,
    previewSelector: ".footer table.table-borderless tr > td:nth-child(3)",
});

din5008ConfigRegistry.add("footer_show_representatives", {
    key: "footer.show_representatives",
    label: _t("Show Representatives"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "boolean",
    default: false,
    previewSelector: ".footer table.table-borderless tr > td:nth-child(3)",
});

din5008ConfigRegistry.add("footer_representatives", {
    key: "footer.representatives",
    label: _t("Representatives"),
    section: "footer",
    sectionLabel: _t("Footer"),
    type: "list",
    default: [],
    previewSelector: ".footer table.table-borderless tr > td:nth-child(3)",
    fields: {
        partner_id: {
            type: "many2one",
            relation: "res.partner",
            label: _t("Contact"),
            placeholder: _t("Search contact..."),
        },
    },
});
