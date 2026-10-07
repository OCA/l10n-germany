import {Component} from "@odoo/owl";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {Din5008ConfigDialog} from "../din5008_config_dialog/din5008_config_dialog.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";

const din5008ConfigRegistry = registry.category("din5008_config_fields");

export class Din5008ConfigField extends Component {
    static template = "l10n_din5008_report_base.Din5008ConfigField";

    static props = {
        ...standardFieldProps,
        options: {type: Object, optional: true},
    };

    setup() {
        this.dialog = useService("dialog");
        this.notification = useService("notification");
    }

    get config() {
        return this._mergeDefaults(
            this._getDefaultConfig(),
            this.props.record.data[this.props.name] || {}
        );
    }

    get dinType() {
        const paperformat = this.props.record.data.paperformat_id;
        const paperformatName = Array.isArray(paperformat)
            ? paperformat[1]
            : (paperformat?.display_name ?? "");

        if (/DIN5008 Type B/i.test(paperformatName)) {
            return "type_b";
        }
        return "type_a";
    }

    get hasOverrides() {
        return Object.keys(this.props.record.data[this.props.name] || {}).length > 0;
    }

    _clone(value) {
        return JSON.parse(JSON.stringify(value ?? {}));
    }

    _getDefaultConfig() {
        const defaults = {};

        for (const field of din5008ConfigRegistry.getAll()) {
            const keys = field.key.split(".");
            let current = defaults;

            for (const key of keys.slice(0, -1)) {
                current[key] ??= {};
                current = current[key];
            }

            const lastKey = keys[keys.length - 1];
            const defaultValue =
                typeof field.default === "function" ? field.default() : field.default;

            if (field.perDinType) {
                current[lastKey] = {
                    type_a: defaultValue,
                    type_b: defaultValue,
                };

                if (field.key === "header.company_logo_position") {
                    current[lastKey].type_a = "right";
                    current[lastKey].type_b = "right";
                } else if (field.key === "header.company_logo_size") {
                    current[lastKey].type_a = 27;
                    current[lastKey].type_b = 45;
                }
            } else {
                current[lastKey] = defaultValue;
            }
        }

        return defaults;
    }

    _mergeDefaults(defaults, overrides) {
        const result = this._clone(defaults);

        for (const [key, value] of Object.entries(overrides || {})) {
            if (
                value &&
                typeof value === "object" &&
                !Array.isArray(value) &&
                result[key] &&
                typeof result[key] === "object" &&
                !Array.isArray(result[key])
            ) {
                result[key] = this._mergeDefaults(result[key], value);
            } else {
                result[key] = value;
            }
        }

        return result;
    }

    _deepEqual(a, b) {
        if (a === b) {
            return true;
        }

        if (
            !a ||
            !b ||
            typeof a !== "object" ||
            typeof b !== "object" ||
            Array.isArray(a) !== Array.isArray(b)
        ) {
            return false;
        }

        const keysA = Object.keys(a);
        const keysB = Object.keys(b);

        if (keysA.length !== keysB.length) {
            return false;
        }

        return keysA.every(
            (key) =>
                Object.prototype.hasOwnProperty.call(b, key) &&
                this._deepEqual(a[key], b[key])
        );
    }

    _getOverrides(config) {
        const defaults = this._getDefaultConfig();
        const overrides = {};

        const compare = (value, defaultValue, target, key) => {
            if (
                value &&
                defaultValue &&
                typeof value === "object" &&
                typeof defaultValue === "object" &&
                !Array.isArray(value) &&
                !Array.isArray(defaultValue)
            ) {
                const nested = {};

                for (const [childKey, childValue] of Object.entries(value)) {
                    compare(childValue, defaultValue[childKey], nested, childKey);
                }

                if (Object.keys(nested).length) {
                    target[key] = nested;
                }
            } else if (!this._deepEqual(value, defaultValue)) {
                target[key] = value;
            }
        };

        for (const [section, values] of Object.entries(config || {})) {
            const nested = {};

            for (const [key, value] of Object.entries(values || {})) {
                compare(value, defaults[section]?.[key], nested, key);
            }

            if (Object.keys(nested).length) {
                overrides[section] = nested;
            }
        }

        return overrides;
    }

    openDialog() {
        const recordData = this.props.record.data;

        const getRelationId = (value) => {
            if (Array.isArray(value)) {
                return value[0] || false;
            }
            return value?.id || false;
        };

        const wizardFields = [
            "company_id",
            "report_layout_id",
            "external_report_layout_id",
            "paperformat_id",
            "font",
            "primary_color",
            "secondary_color",
            "report_header",
            "report_footer",
            "layout_background",
            "company_details",
            "qr_code",
            "account_number",
        ];

        const wizardValues = {};

        for (const field of wizardFields) {
            const value = recordData[field];

            if (value === undefined) {
                continue;
            }

            if (
                [
                    "company_id",
                    "report_layout_id",
                    "external_report_layout_id",
                    "paperformat_id",
                ].includes(field)
            ) {
                wizardValues[field] = getRelationId(value);
            } else {
                wizardValues[field] = value;
            }
        }

        this.dialog.add(Din5008ConfigDialog, {
            config: this._clone(this.config),
            dinType: this.dinType,
            getWizardValues: () => this._clone(wizardValues),
            onApply: async (newConfig) => {
                await this.props.record.update({
                    [this.props.name]: this._getOverrides(newConfig),
                });
            },
        });
    }

    resetConfig() {
        this.dialog.add(ConfirmationDialog, {
            title: _t("Reset DIN 5008 Configuration"),
            body: _t(
                "Are you sure you want to reset the configuration to its default values?"
            ),
            confirmLabel: _t("Reset"),
            cancelLabel: _t("Cancel"),
            confirm: async () => {
                await this.props.record.update({
                    [this.props.name]: {},
                });
            },
        });
    }
}

registry.category("fields").add("din5008_config", {
    component: Din5008ConfigField,
    supportedTypes: ["json"],
});
