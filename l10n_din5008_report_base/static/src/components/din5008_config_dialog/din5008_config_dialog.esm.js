import {Component, onMounted, onWillUnmount, useRef, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

const din5008ConfigRegistry = registry.category("din5008_config_fields");

export class Din5008ConfigDialog extends Component {
    static template = "l10n_din5008_report_base.Din5008ConfigDialog";
    static components = {Dialog};

    static props = {
        close: Function,
        config: Object,
        onApply: Function,
        getWizardValues: Function,
        dinType: {type: String, optional: true},
    };

    setup() {
        this.highlightPreviewField = this.highlightPreviewField.bind(this);

        this.notification = useService("notification");
        this.orm = useService("orm");
        this.previewFrameRef = useRef("previewFrame");

        this.activePreviewSelector = null;
        this.previewTimer = null;
        this.previewRequestId = 0;

        this.state = useState({
            config: this._clone(this.props.config),
            expandedSections: {},
            activeSection: null,
            previewHtml: "",
            previewLoading: false,
        });

        onMounted(() => {
            this.refreshPreview();
        });

        onWillUnmount(() => {
            clearTimeout(this.previewTimer);
            this.previewRequestId++;
        });
    }

    _clone(value) {
        return JSON.parse(JSON.stringify(value ?? {}));
    }

    get sections() {
        const sections = new Map();

        for (const field of din5008ConfigRegistry.getAll()) {
            const name = field.section || "din5008";

            if (!sections.has(name)) {
                sections.set(name, {
                    name,
                    label: field.sectionLabel || name,
                    priority: field.sectionPriority ?? 100,
                    fields: [],
                });
            }

            const section = sections.get(name);
            section.fields.push(field);
            section.priority = Math.min(section.priority, field.sectionPriority ?? 100);
        }

        return Array.from(sections.values()).sort(
            (a, b) => a.priority - b.priority || a.name.localeCompare(b.name)
        );
    }

    get dinType() {
        return this.props.dinType || "type_a";
    }

    toggleSection = (name) => {
        this.state.expandedSections[name] = !this.state.expandedSections[name];

        if (this.state.expandedSections[name]) {
            this.state.activeSection = name;
        } else if (this.state.activeSection === name) {
            this.state.activeSection = null;
        }
    };

    isSectionExpanded(name) {
        return Boolean(this.state.expandedSections[name]);
    }

    getValue(field) {
        let value = this.state.config;

        for (const key of field.key.split(".")) {
            if (!value || typeof value !== "object") {
                value = undefined;
                break;
            }

            value = value[key];
        }

        if (field.perDinType) {
            value =
                value && typeof value === "object" && !Array.isArray(value)
                    ? value[this.dinType]
                    : undefined;
        }

        return value ?? this._getDefaultValueForType(field);
    }

    _getDefaultValueForType(field) {
        if (field.perDinType) {
            if (field.key === "header.company_logo_position") {
                return "right";
            }

            if (field.key === "header.company_logo_size") {
                return this.dinType === "type_b" ? 45 : 27;
            }
        }

        return this._getDefaultValue(field);
    }

    _getDefaultValue(field) {
        return typeof field.default === "function" ? field.default() : field.default;
    }

    setValue(field, value) {
        const keys = field.key.split(".");
        let current = this.state.config;

        for (const key of keys.slice(0, -1)) {
            if (
                !current[key] ||
                typeof current[key] !== "object" ||
                Array.isArray(current[key])
            ) {
                current[key] = {};
            }

            current = current[key];
        }

        const lastKey = keys[keys.length - 1];

        if (field.perDinType) {
            if (
                !current[lastKey] ||
                typeof current[lastKey] !== "object" ||
                Array.isArray(current[lastKey])
            ) {
                current[lastKey] = {
                    type_a: field.key === "header.company_logo_size" ? 27 : "right",
                    type_b: field.key === "header.company_logo_size" ? 45 : "right",
                };
            }

            current[lastKey][this.dinType] = value;
        } else {
            current[lastKey] = value;
        }

        this.schedulePreview();
    }

    getSelectionOptions(field) {
        if (typeof field.options === "function") {
            return field.options(this.state.config, this.env.lang) || [];
        }

        return field.options || [];
    }

    updateFloat = (field, value) => {
        if (value === "" || value === null) {
            return;
        }

        let number = Number.parseFloat(value);

        if (!Number.isFinite(number)) {
            return;
        }

        if (field.min !== undefined) {
            number = Math.max(field.min, number);
        }

        if (field.max !== undefined) {
            number = Math.min(field.max, number);
        }

        this.setValue(field, number);
    };

    updateBoolean = (field, value) => {
        this.setValue(field, Boolean(value));
    };

    updateSelection = (field, value) => {
        this.setValue(field, value);
    };

    updateText = (field, value) => {
        this.setValue(field, value);
    };

    getListFields(field) {
        return Object.entries(field.fields || {});
    }

    getListValue(field) {
        const value = this.getValue(field);
        return Array.isArray(value) ? value : [];
    }

    addListItem = (field) => {
        const item = {};

        for (const [name, subField] of this.getListFields(field)) {
            switch (subField.type) {
                case "translated_text":
                    item[name] = {};
                    break;
                case "text":
                    item[name] = "";
                    break;
                case "boolean":
                    item[name] = false;
                    break;
                case "float":
                    item[name] = subField.default ?? 0;
                    break;
                case "selection":
                    item[name] = subField.default ?? "";
                    break;
                default:
                    item[name] = subField.default ?? "";
            }
        }

        this.setValue(field, [...this.getListValue(field), item]);
    };

    removeListItem = (field, index) => {
        const items = [...this.getListValue(field)];
        items.splice(index, 1);
        this.setValue(field, items);
    };

    updateListField = (field, index, name, value) => {
        const items = this.getListValue(field).map((item) => ({
            ...item,
        }));

        if (!items[index]) {
            return;
        }

        items[index][name] = value;
        this.setValue(field, items);
    };

    getTranslatedText(value) {
        if (typeof value === "string") {
            return value;
        }

        return value?.[this.env.lang] || "";
    }

    updateListTranslatedText = (field, index, name, value) => {
        const item = this.getListValue(field)[index];

        if (!item) {
            return;
        }

        const translations = {
            ...(item[name] || {}),
            [this.env.lang]: value,
        };

        this.updateListField(field, index, name, translations);
    };

    // ---------------------------------------------------------
    // Preview highlighting
    // ---------------------------------------------------------

    _getPreviewSelector(field) {
        // A registry field can define its own exact report selector.
        if (field.previewSelector) {
            return Array.isArray(field.previewSelector)
                ? field.previewSelector.join(", ")
                : field.previewSelector;
        }

        const key = field.key || "";

        if (key.startsWith("header.")) {
            return ".company_header";
        }

        if (key.startsWith("sender.")) {
            return "#din5008_report_main_address, .address";
        }

        if (key.startsWith("receiver.")) {
            return ".information_block";
        }

        if (key.startsWith("footer.") || key.startsWith("company_details.")) {
            return ".company_details, .din_page.footer";
        }

        if (key.startsWith("page.")) {
            return ".din_page";
        }

        if (key.startsWith("marks.")) {
            return [
                ".din5008_marks",
                ".din5008_fold",
                ".din5008_fold_1",
                ".din5008_fold_2",
                ".din5008_hole",
            ].join(", ");
        }

        // Fallback for fields whose key is not covered above.
        if (key.includes("logo")) {
            return ".company_header";
        }

        if (key.includes("fold") || key.includes("hole")) {
            return ".din5008_marks, .din5008_fold, .din5008_hole";
        }

        return null;
    }

    highlightPreviewField(field) {
        this.activePreviewSelector = this._getPreviewSelector(field);
        this._applyPreviewHighlight();
    }

    _applyPreviewHighlight() {
        const iframe = this.previewFrameRef.el;
        const doc = iframe?.contentDocument;

        if (!doc) {
            return;
        }

        // Add the highlighting CSS inside the iframe itself.
        if (!doc.getElementById("din5008-config-highlight-style")) {
            const style = doc.createElement("style");
            style.id = "din5008-config-highlight-style";
            style.textContent = `
                .din5008-config-highlight {
                    outline: 1px dashed #0d6efd !important;
                    outline-offset: 1px !important;
                    background-color: rgba(13, 110, 253, 0.14) !important;
                    box-shadow: none !important;
                }
            `;

            (doc.head || doc.documentElement).appendChild(style);
        }

        // Clear the previous selection.
        doc.querySelectorAll(".din5008-config-highlight").forEach((element) => {
            element.classList.remove("din5008-config-highlight");
        });

        if (!this.activePreviewSelector) {
            return;
        }

        // Highlight all elements matching the selected field.
        try {
            const elements = doc.querySelectorAll(this.activePreviewSelector);

            elements.forEach((element) => {
                element.classList.add("din5008-config-highlight");
            });

            if (!elements.length) {
                console.warn(
                    "No report element found for DIN 5008 field:",
                    this.activePreviewSelector
                );
            }
        } catch (error) {
            console.warn(
                "Invalid DIN 5008 preview selector:",
                this.activePreviewSelector,
                error
            );
        }
    }

    schedulePreview() {
        clearTimeout(this.previewTimer);

        this.previewTimer = setTimeout(() => {
            this.refreshPreview();
        }, 300);
    }

    _preparePreviewHtml(html) {
        return html || "";
    }

    async refreshPreview() {
        const requestId = ++this.previewRequestId;
        this.state.previewLoading = true;

        try {
            const wizardValues = this.props.getWizardValues();

            const html = await this.orm.call(
                "base.document.layout",
                "action_get_din5008_preview",
                [wizardValues, this._clone(this.state.config)]
            );

            if (requestId !== this.previewRequestId) {
                return;
            }

            const previewHtml = this._preparePreviewHtml(html || "");
            this.state.previewHtml = previewHtml;

            const iframe = this.previewFrameRef.el;

            if (!iframe) {
                console.error("DIN5008 preview iframe not found");
                return;
            }

            iframe.style.visibility = "hidden";

            iframe.onload = () => {
                // Reapply the selected field after every preview reload.
                this._applyPreviewHighlight();
                iframe.style.visibility = "visible";
            };

            iframe.srcdoc = previewHtml;
        } catch (error) {
            if (requestId === this.previewRequestId) {
                this.state.previewHtml = "";

                if (this.previewFrameRef.el) {
                    this.previewFrameRef.el.srcdoc = "";
                }

                console.error("DIN 5008 preview error:", error);

                this.notification.add(_t("The DIN 5008 preview could not be loaded."), {
                    type: "danger",
                });
            }
        } finally {
            if (requestId === this.previewRequestId) {
                this.state.previewLoading = false;
            }
        }
    }

    apply = async () => {
        for (const section of this.sections) {
            for (const field of section.fields) {
                if (typeof field.validate !== "function") {
                    continue;
                }

                if (!field.validate(this.getValue(field))) {
                    this.notification.add(
                        field.validationError || _t("The value is invalid."),
                        {type: "warning"}
                    );
                    return;
                }
            }
        }

        await this.props.onApply(this._clone(this.state.config));
        this.props.close();
    };
}
