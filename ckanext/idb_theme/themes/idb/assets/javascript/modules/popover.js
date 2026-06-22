/**
 * A module to initialize Bootstrap popovers on elements with content from a specified selector.
 */
ckan.module("popover", function () {
    return {
        options: {
            popoverContent: null,
            title: null,
        },
        initialize() {
            const content = document.querySelector(this.options.popoverContent);
            if (!content) {
                console.warn("Cannot locate popover content with selector %o for %o", this.options.popoverContent, this.el[0]);
                return;
            }

            const title = this.options.title || content.dataset.popoverTitle;

            bootstrap.Popover.getOrCreateInstance(this.el[0], {
                content: content.innerHTML,
                title: title,
                html: true,
            });
        }
    }
})
