import {onMounted, onWillUnmount, useEffect} from "@odoo/owl";
import {IframeWrapperField} from "@web/views/fields/iframe_wrapper/iframe_wrapper_field";
import {patch} from "@web/core/utils/patch";
/**
 * Highlight an area of the document layout preview while a field is focused.
 *
 * A field (or any element) of the form carrying a class
 * ``o_report_preview_highlight_<key>`` sets ``data-report-preview-highlight="<key>"``
 * on the root element of the preview document while it has the focus. The
 * report stylesheets outline the matching area, e.g. the footer for ``footer``.
 */
const CLASS_PREFIX = "o_report_preview_highlight_";

patch(IframeWrapperField.prototype, {
    setup() {
        super.setup();
        this.previewHighlight = null;
        this.onPreviewFocusIn = (ev) => {
            this.previewHighlight = this.getPreviewHighlightKey(ev.target);
            this.applyPreviewHighlight();
        };
        this.onPreviewFocusOut = () => {
            this.previewHighlight = null;
            this.applyPreviewHighlight();
        };
        let form = null;
        onMounted(() => {
            form = this.iframeRef.el.closest(".o_form_view");
            if (form) {
                form.addEventListener("focusin", this.onPreviewFocusIn);
                form.addEventListener("focusout", this.onPreviewFocusOut);
            }
        });
        onWillUnmount(() => {
            if (form) {
                form.removeEventListener("focusin", this.onPreviewFocusIn);
                form.removeEventListener("focusout", this.onPreviewFocusOut);
            }
        });
        // Runs after the effect writing the preview document
        useEffect(
            () => this.applyPreviewHighlight(),
            () => [this.props.record.data[this.props.name]]
        );
    },

    getPreviewHighlightKey(element) {
        const holder = element?.closest?.(`[class*="${CLASS_PREFIX}"]`);
        if (!holder) {
            return null;
        }
        for (const className of holder.classList) {
            if (className.startsWith(CLASS_PREFIX)) {
                return className.slice(CLASS_PREFIX.length);
            }
        }
        return null;
    },

    applyPreviewHighlight() {
        const root = this.iframeRef.el?.contentDocument?.documentElement;
        if (!root) {
            return;
        }
        if (this.previewHighlight) {
            root.dataset.reportPreviewHighlight = this.previewHighlight;
        } else {
            delete root.dataset.reportPreviewHighlight;
        }
    },
});
