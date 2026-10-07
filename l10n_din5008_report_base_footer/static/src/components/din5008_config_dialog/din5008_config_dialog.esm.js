import {Din5008ConfigDialog} from "@l10n_din5008_report_base/components/din5008_config_dialog/din5008_config_dialog.esm";
import {Many2XAutocomplete} from "@web/views/fields/relational_utils";
import {onWillStart} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

Din5008ConfigDialog.components = {
    ...Din5008ConfigDialog.components,
    Many2XAutocomplete,
};

patch(Din5008ConfigDialog.prototype, {
    setup() {
        super.setup(...arguments);

        this.orm = useService("orm");
        this.state.partnerNames = {};

        onWillStart(async () => {
            const field = this.sections
                .flatMap((section) => section.fields)
                .find((entry) => entry.key === "footer.representatives");

            if (!field) {
                return;
            }

            const ids = [
                ...new Set(
                    this.getListValue(field)
                        .map((item) => item.partner_id)
                        .filter(Boolean)
                ),
            ];

            if (!ids.length) {
                return;
            }

            const records = await this.orm.read("res.partner", ids, ["display_name"]);

            for (const record of records) {
                this.state.partnerNames[record.id] = record.display_name || "";
            }
        });
    },

    getMany2oneProps(field, index, name, subField) {
        const item = this.getListValue(field)[index];
        const partnerId = item?.[name] || false;

        return {
            resModel: subField.relation || "res.partner",
            fieldString: subField.label || name,
            value: this.state.partnerNames[partnerId] || "",
            activeActions: {
                create: true,
                createEdit: true,
                write: true,
            },
            getDomain: () => [],
            update: (selection) => {
                const selected = selection?.[0] || false;

                this.updateListField(
                    field,
                    index,
                    name,
                    selected ? selected.id : false
                );

                if (selected) {
                    this.state.partnerNames[selected.id] =
                        selected.display_name || selected.name || "";
                } else if (partnerId) {
                    delete this.state.partnerNames[partnerId];
                }
            },
            placeholder: subField.placeholder || "Search contact...",
        };
    },
});
