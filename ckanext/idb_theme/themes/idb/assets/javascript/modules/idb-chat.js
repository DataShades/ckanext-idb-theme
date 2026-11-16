this.ckan.module("idb-chat", function ($) {
  return {
    initialize() {
      this._onOverlayClick = this._onOverlayClick.bind(this);
      this._onRendered = this._onRendered.bind(this);
      this._onAnswer = this._onAnswer.bind(this);
      this.el.on("click", this._onOverlayClick);

      this.modal = $("#knowledge-assistant-modal");
      this.modal.on("ka:rendered", this._onRendered);
      this.modal.on("ka:answer", this._onAnswer);
    },

    _onAnswer(event, message, text) {
      const template = document.getElementById("idb-chat-answer-template");
      if (!template) return;

      const parts = $(template.content.cloneNode(true));
      const copy = parts.find(".idb-chat-copy");
      copy.attr("data-module-copy-value", ($(message).find(".ka-message-prose").text() || text).trim());

      $(message).prepend(parts.find(".idb-chat-cot")).append(parts.find(".idb-chat-answer-actions"));
      ckan.module.initializeElement(copy[0]);
    },

    _onOverlayClick() {
      $("#knowledge-assistant-modal .ka-close-btn").trigger("click");
    },

    _onRendered(event, element) {
      this._setTimes(element);
    },

    _setTimes(element) {
      const now = new Date();
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);

      $(element)
        .find("time[datetime]")
        .each(function () {
          const date = new Date($(this).attr("datetime"));
          if (isNaN(date.getTime())) return;

          const minutes = Math.max(1, Math.floor((now - date) / 60000));
          let text;
          if (minutes < 60) {
            text = ckan.i18n._("%(n)sm ago", { n: minutes });
          } else if (date.toDateString() === now.toDateString()) {
            text = ckan.i18n._("%(n)sh ago", { n: Math.floor(minutes / 60) });
          } else if (date.toDateString() === yesterday.toDateString()) {
            text = ckan.i18n._("Yesterday");
          } else {
            const options = { month: "short", day: "numeric" };
            if (date.getFullYear() !== now.getFullYear()) options.year = "numeric";
            text = date.toLocaleDateString(document.documentElement.lang || undefined, options);
          }

          $(this).text(text);
        });
    },
  };
});
