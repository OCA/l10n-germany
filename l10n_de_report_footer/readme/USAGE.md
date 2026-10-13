Print any report using a document layout. The footer text is printed with
the placeholders replaced by the data of the company that issues the
document; the company block prints the tax numbers enabled in the document
layout, followed by the footer lines added by other modules.

Developers: call `<t t-call="l10n_de_report_footer.footer_lines"/>` inside a
`<ul>` of a custom layout and add `<li>` elements to the hook
`//t[@name='l10n_de_report_footer_lines']` of that template to print
additional lines in every layout. The template receives `company` either as
the company or, in the wizard preview, as the wizard; read company fields
through `company._get_report_footer_company_field("field")`. Give a form
field the class `o_report_preview_highlight_<key>` and style
`html[data-report-preview-highlight="<key>"] <selector>` in the report assets
to outline an area of the layout preview while the field is focused.

Developers: register a layout setting instead of adding a field to the
company and to the wizard. Inherit the mixin `report.layout.config.mixin` and
append the declaration to `_get_report_layout_config_fields()`:

```python
class ReportLayoutConfigMixin(models.AbstractModel):
    _inherit = "report.layout.config.mixin"

    def _get_report_layout_config_fields(self):
        return super()._get_report_layout_config_fields() + [
            {
                "key": "my_module.show_bank",
                "label": self.env._("Print Bank Account"),
                "section": "my_module",
                "section_label": self.env._("My Layout"),
                "section_sequence": 50,
                "type": "boolean",
                "default": True,
                # optional: "min", "max", "step", "allow_zero" (numbers),
                # "options": [(value, label), ...] (selection, or presets
                # offered next to the text input of a char setting),
                # "maxlength" (char), "validate": "_my_check" (method of
                # the mixin raising ValidationError), "help",
                # "highlight": "footer", "visible_if": {"other.key": True},
                # "layouts": ["my_module.external_layout_x"]
            }
        ]
```

The value is stored in the JSON field `report_layout_config` of the company
under its key and validated against the declaration when the company is
written. Read it in templates and code with
`company._get_report_layout_config_value("my_module.show_bank")`, which
returns the declared default while nothing is stored. The wizard offers the
setting on the tab of its section for the layouts listed in `layouts` (all
layouts when absent). Use `_get_report_footer_section()` to add a setting to
the *Footer* tab and `_get_report_footer_scope_class()` to scope CSS printed
in a `<style>` element inside the footer of a layout.
