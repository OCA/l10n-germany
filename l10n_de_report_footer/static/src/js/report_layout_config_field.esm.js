import {Component, useState} from "@odoo/owl";
import {CheckBox} from "@web/core/checkbox/checkbox";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

/**
 * Widget of the JSON field holding the layout settings of the company.
 *
 * The settings are declared on the server (``_get_report_layout_config_fields``)
 * and passed through a second JSON field of the record (``specField``), one
 * dictionary per setting with its key, type, label, default and section. The
 * widget renders one tab per section and writes every change into the record,
 * so the layout preview follows the unsaved values. A setting carrying a
 * ``highlight`` key outlines the matching area of the preview while focused
 * (see report_preview_highlight.esm.js).
 */
export class ReportLayoutConfigField extends Component {
    static template = "l10n_de_report_footer.ReportLayoutConfigField";
    static components = {CheckBox};
    static props = {
        ...standardFieldProps,
        specField: {type: String, optional: true},
    };
    static defaultProps = {
        specField: "report_layout_config_fields",
    };

    setup() {
        this.state = useState({section: null});
    }

    get config() {
        return this.props.record.data[this.props.name] || {};
    }

    get specs() {
        return this.props.record.data[this.props.specField] || [];
    }

    get sections() {
        const sections = new Map();
        for (const spec of this.specs) {
            const name = spec.section || "default";
            if (!sections.has(name)) {
                sections.set(name, {
                    name,
                    label: spec.section_label || name,
                    sequence: spec.section_sequence ?? 100,
                    fields: [],
                });
            }
            sections.get(name).fields.push(spec);
        }
        return [...sections.values()].sort((a, b) => a.sequence - b.sequence);
    }

    get currentSection() {
        const sections = this.sections;
        return sections.find((s) => s.name === this.state.section) || sections[0];
    }

    selectSection(name) {
        this.state.section = name;
    }

    inputId(spec) {
        return `${this.props.id || this.props.name}_${spec.key.replace(/\W/g, "_")}`;
    }

    value(spec) {
        return spec.key in this.config ? this.config[spec.key] : spec.default;
    }

    isVisible(spec) {
        const config = this.config;
        return Object.entries(spec.visible_if || {}).every(([key, expected]) => {
            const other = this.specs.find((s) => s.key === key);
            const value = key in config ? config[key] : other?.default;
            return value === expected;
        });
    }

    rowClass(spec) {
        const classes = ["o_report_layout_config_field", "row", "mb-2"];
        if (spec.highlight) {
            classes.push(`o_report_preview_highlight_${spec.highlight}`);
        }
        return classes.join(" ");
    }

    /**
     * Store a value; an empty numeric input restores the declared default.
     */
    onChange(spec, raw) {
        let value = raw;
        if (spec.type === "integer" || spec.type === "float") {
            value = spec.type === "integer" ? parseInt(raw, 10) : parseFloat(raw);
            if (Number.isNaN(value)) {
                value = undefined;
            }
        }
        const config = {...this.config};
        if (value === undefined) {
            delete config[spec.key];
        } else {
            config[spec.key] = value;
        }
        this.props.record.update({[this.props.name]: config});
    }
}

export const reportLayoutConfigField = {
    component: ReportLayoutConfigField,
    displayName: _t("Report Layout Configuration"),
    supportedTypes: ["json"],
    extractProps: ({options}) =>
        options.spec_field ? {specField: options.spec_field} : {},
};

registry.category("fields").add("report_layout_config", reportLayoutConfigField);
