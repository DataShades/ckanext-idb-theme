import { contentAsText } from "./util";

export class Notification implements INotification {
    static styles: Record<
        string,
        {
            btnClose: string;
            main: string;
            border: string;
            progress: string;
        }
    > = {
        secondary: {
            btnClose: "btn-close-white",
            main: "text-white bg-secondary",
            border: "border-secondary",
            progress: "bg-secondary",
        },
        light: {
            btnClose: "",
            main: "text-dark bg-light border-bottom border-dark",
            border: "border-dark",
            progress: "bg-dark",
        },
        white: {
            btnClose: "",
            main: "text-dark bg-white border-bottom border-dark",
            border: "border-dark",
            progress: "bg-dark",
        },
        dark: {
            btnClose: "btn-close-white",
            main: "text-white bg-dark",
            border: "border-dark",
            progress: "bg-dark",
        },
        info: {
            btnClose: "btn-close-white",
            main: "text-white bg-info",
            border: "border-info",
            progress: "bg-info",
        },
        primary: {
            btnClose: "btn-close-white",
            main: "text-white bg-primary",
            border: "border-primary",
            progress: "bg-primary",
        },
        success: {
            btnClose: "btn-close-white",
            main: "text-white bg-success",
            border: "border-success",
            progress: "bg-success",
        },
        warning: {
            btnClose: "btn-close-white",
            main: "text-white bg-warning",
            border: "border-warning",
            progress: "bg-warning",
        },
        danger: {
            btnClose: "btn-close-white",
            main: "text-white bg-danger",
            border: "border-danger",
            progress: "bg-danger",
        },
        default: {
            btnClose: "",
            main: "",
            border: "",
            progress: "bg-primary",
        },
    };

    static positions: Record<string, string> = {
        "top-left": "top-0 start-0 ms-1 mt-1",
        "top-center": "top-0 start-50 translate-middle-x mt-1",
        "top-right": "top-0 end-0 me-1 mt-1",
        "middle-left": "top-50 start-0 translate-middle-y ms-1",
        "middle-center": "top-50 start-50 translate-middle p-3",
        "middle-right": "top-50 end-0 translate-middle-y me-1",
        "bottom-left": "bottom-0 start-0 ms-1 mb-1",
        "bottom-center": "bottom-0 start-50 translate-middle-x mb-1",
        "bottom-right": "bottom-0 end-0 me-1 mb-1",
    };
    static containerClass: string = "toast-container";

    #toast: bootstrap.Toast;
    constructor(public el: HTMLElement) {
        // @ts-ignore
        this.#toast = bootstrap.Toast.getOrCreateInstance(el);
    }
    close() {
        this.#toast.hide();
    }
    show() {
        this.#toast.show();
    }
    destroy() {
        this.#toast.dispose();
    }

    static #createToastContainer(position: string, style: string) {
        const containerID = `${this.containerClass}-${position}`;
        const container = document.getElementById(containerID);

        if (container) return container;

        const wrapper = document.createElement("div");
        const positionClasses =
            this.positions[position] || this.positions["bottom-right"];

        wrapper.classList.add("position-relative");
        wrapper.setAttribute("role", style === "danger" ? "alert" : "status");
        wrapper.setAttribute(
            "aria-live",
            style === "danger" ? "assertive" : "polite",
        );
        wrapper.setAttribute("aria-atomic", "true");

        wrapper.innerHTML = `<div id="${containerID}" class="toast-container position-fixed pb-1 ${positionClasses}"></div>`;
        document.body.appendChild(wrapper);
        return document.getElementById(containerID)!;
    }

    static count: number = 0;

    static create(
        content: Theming.Content,
        options: Theming.INotificationParams = {},
    ) {
        const styleName = options.style || "default";
        const opts = {
            title: "",
            icon: "",
            subtitle: "",
            delay: options.dismissible ? 3000 : 0,
            position: "bottom-right",
            showProgress: true,
            stacking: true,
            ...options,
        };

        const style =
            Notification.styles[styleName] || Notification.styles.default!;
        const containerEl = Notification.#createToastContainer(
            opts.position,
            styleName,
        );

        const toastEl = document.createElement("div");
        const toastID = `toast-${++Notification.count}`;

        toastEl.setAttribute("id", toastID);
        toastEl.setAttribute("role", "alert");
        toastEl.setAttribute("aria-live", "assertive");
        toastEl.setAttribute("aria-atomic", "true");
        toastEl.classList.add("toast", "align-items-center");
        style.border && toastEl.classList.add(style.border);

        toastEl.innerHTML = `
              <div class="toast-header ${style.main}">
                ${opts.icon}
                <strong class="me-auto">${opts.title}</strong>
                <small>${opts.subtitle}</small>
                <button type="button" class="btn-close ${style.btnClose}" data-bs-dismiss="toast" aria-label="Close"></button>
              </div>
              <div class="toast-body position-relative">${contentAsText(content)}</div>
            `;

        if (!opts.stacking) {
            containerEl.querySelectorAll(".toast").forEach((el) => el.remove());
        }

        containerEl.appendChild(toastEl);

        toastEl.dataset.bsDelay = String(opts.delay);
        toastEl.dataset.bsAutohide = String(opts.delay > 0);

        if (opts.delay && opts.showProgress) {
            const progressEl = Notification.#createProgressBar(
                opts.delay,
                style.progress,
            );

            // reset progress bar to 100% on mouse enter
            toastEl.addEventListener("mouseenter", function () {
                progressEl.style.animation = "none";
                progressEl.style.width = "100%";
            });

            // restart progress bar animation on mouse leave
            toastEl.addEventListener("mouseleave", function () {
                progressEl.style.animation = `reverseProgress ${opts.delay / 1000}s linear forwards`;
            });

            toastEl.querySelector(".toast-body")?.appendChild(progressEl);
        }

        return new Notification(toastEl);
    }

    static #createProgressBar = function (delay: number, cls: string) {
        const progressEl = document.createElement("div");

        progressEl.classList.add(
            "progress-bar-timer",
            "position-absolute",
            "bottom-0",
            "start-0",
        );
        progressEl.classList.add(cls);

        progressEl.style.height = "3px";
        progressEl.style.borderBottomLeftRadius = "0.25rem";
        progressEl.style.animation = `reverseProgress ${delay / 1000}s linear forwards`;

        return progressEl;
    };

    static byId(id: string) {
        const el = document.getElementById(id);
        if (!el) {
            return null;
        }
        return new Notification(el);
    }
}
