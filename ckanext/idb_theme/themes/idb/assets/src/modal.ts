import { button } from "./util";

export class Modal implements IModal<HTMLElement> {
    #modal!: bootstrap.Modal;
    constructor(public el: HTMLElement) {
        // @ts-ignore
        this.#modal = bootstrap.Modal.getOrCreateInstance(el);
    }

    destroy() {
        this.#modal.dispose();
    }

    show() {
        this.#modal.show();
    }

    close() {
        this.#modal.hide();
    }

    static create(content: Theming.Content, params: Theming.IModalParams = {}) {
        const html = `
        <div class="modal fade" tabindex="-1" aria-hidden="true">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header"></div>
              <div class="modal-body"></div>
              <div class="modal-footer"></div>
            </div>
          </div>
        </div>`;

        document.body.insertAdjacentHTML("beforeend", html);
        const modal = document.body.lastElementChild! as HTMLElement;

        if (params.title) {
            modal
                .querySelector(".modal-header")
                ?.insertAdjacentHTML(
                    "beforeend",
                    `<h5 class="modal-title">${params.title}</h5>`,
                );
        }

        if (params.dismissible) {
            modal
                .querySelector(".modal-header")
                ?.insertAdjacentHTML(
                    "beforeend",
                    `<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>`,
                );
        }

        modal.querySelector(".modal-body")?.append(content);

        const actions = params.actions || [];
        if (params.dismissLabel) {
            actions.unshift(
                button(params.dismissLabel, {
                    props: { onclick: () => result.close() },
                    style: "secondary",
                }),
            );
        }

        if (actions.length) {
            modal.querySelector(".modal-footer")?.append(...actions);
        }

        const result = new Modal(modal);

        return result;
    }

    static byId(id: string): Modal | null {
        const el = document.getElementById(id);
        if (!el) {
            return null;
        }
        return new Modal(<HTMLElement>el);
    }
}
