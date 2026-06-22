export class Popover implements IPopover {
    #popover: bootstrap.Popover;
    constructor(public el: HTMLElement) {
        // @ts-ignore
        this.#popover = bootstrap.Popover.getOrCreateInstance(el);
    }
    close() {
        this.#popover.hide();
    }
    show() {
        this.#popover.show();
    }
    destroy() {
        this.#popover.dispose();
    }

    static create(
        content: Theming.Content,
        props: Theming.IPopoverParams = { target: document.body },
    ): Popover {
        props.target.dataset.bsContent =
            typeof content === "string" ? content : content.textContent!;
        props.target.dataset.bsHtml = "true";
        if (props.title) {
            props.target.dataset.bsTitle = props.title;
        }
        if (props.trigger) {
            props.target.dataset.bsTrigger = props.trigger;
        }

        return new Popover(props.target);
    }
    static byId(id: string) {
        const el = document.getElementById(id);
        if (!el) {
            return null;
        }
        return new Popover(el);
    }
}
