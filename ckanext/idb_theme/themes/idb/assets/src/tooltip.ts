export class Tooltip implements ITooltip {
    #tooltip: bootstrap.Tooltip;
    constructor(public el: HTMLElement) {
        // @ts-ignore
        this.#tooltip = bootstrap.Tooltip.getOrCreateInstance(el);
    }
    close() {
        this.#tooltip.hide();
    }
    show() {
        this.#tooltip.show();
    }
    destroy() {
        this.#tooltip.dispose();
    }

    static create(
        content: Theming.Content,
        props: Theming.ITooltipParams = { target: document.body },
    ): Tooltip {
        if (typeof content !== "string") {
            throw "Only string tooltips are supported";
        }
        props.target.dataset.bsTitle = content;
        if (props.position) {
            props.target.dataset.bsPlacement = props.position;
        }
        return new Tooltip(props.target);
    }
    static byId(id: string) {
        const el = document.getElementById(id);
        if (!el) {
            return null;
        }
        return new Tooltip(el);
    }
}
