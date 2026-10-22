/*
 * Styled dropdown on top of a native select. The select stays in the form
 * (hidden), so it is submitted as usual and works without JavaScript. Picking
 * an option updates the select and fires its "change" event, so htmx triggers
 * and forms listening to it keep working.
 *
 * Keyboard: Enter, Space, ArrowUp and ArrowDown open the list; ArrowUp,
 * ArrowDown, Home and End move between the options; Enter and Space pick the
 * option; Escape and Tab close the list.
 *
 * Examples
 *
 * <label for="field-sort">Order by</label>
 * <select id="field-sort" name="sort" class="form-select" data-module="idb-select">
 *   <option value="name asc" selected>Name</option>
 *   <option value="metadata_modified desc">Last modified</option>
 * </select>
 *
 */
this.ckan.module("idb-select", function ($) {
  "use strict";
  return {
    initialize: function () {
      var select = this.el[0];
      var id = select.id || "idb-select-" + Math.random().toString(36).slice(2);

      this.select = select;
      this.label = select.id ? document.querySelector('label[for="' + select.id + '"]') : null;

      this.wrapper = $('<div class="idb-select"></div>');
      this.trigger = $('<button type="button" class="idb-select-trigger" role="combobox" aria-haspopup="listbox" aria-expanded="false"></button>')
        .addClass(select.className)
        .attr({ id: id + "-trigger", "aria-controls": id + "-listbox" })
        .prop("disabled", select.disabled);
      this.list = $('<ul class="idb-select-options" role="listbox" tabindex="-1" hidden></ul>').attr("id", id + "-listbox");

      $.each(select.options, function (index, option) {
        $('<li class="idb-select-option" role="option"></li>')
          .attr("id", id + "-option-" + index)
          .text(option.text)
          .appendTo(this.list);
      }.bind(this));
      this.options = this.list.children();

      // the label names the visible control instead of the hidden select
      if (this.label) {
        this.label.id = this.label.id || id + "-label";
        this.label.htmlFor = this.trigger.attr("id");
        this.list.attr("aria-labelledby", this.label.id);
      }

      this.wrapper.append(this.trigger, this.list).insertAfter(select);
      select.hidden = true;
      this._render();

      // the focus stays on the trigger while the list is open: the list
      // closes when it moves away, e.g. on a click outside of the dropdown
      this.trigger.on("click", this._onTriggerClick.bind(this));
      this.trigger.on("keydown", this._onKeydown.bind(this));
      this.trigger.on("blur", this._close.bind(this));
      this.list.on("mousedown", function (event) { event.preventDefault(); });
      this.list.on("click", ".idb-select-option", this._onOptionClick.bind(this));
      this.list.on("mousemove", ".idb-select-option", this._onOptionHover.bind(this));
    },

    teardown: function () {
      if (this.label) {
        this.label.htmlFor = this.select.id;
      }
      this.wrapper.remove();
      this.select.hidden = false;
    },

    _isOpen: function () {
      return this.trigger.attr("aria-expanded") === "true";
    },

    /* Shows the selected option on the trigger and in the list. */
    _render: function () {
      var selected = this.select.selectedIndex;

      this.trigger.text(selected >= 0 ? this.select.options[selected].text : "");
      this.options.each(function (index, option) {
        $(option).attr("aria-selected", index === selected ? "true" : "false");
      });
    },

    _open: function () {
      if (this.select.disabled || this._isOpen()) {
        return;
      }
      // Safari does not focus buttons on click, the blur closes the list
      this.trigger.trigger("focus");
      this.list.prop("hidden", false);
      this.trigger.attr("aria-expanded", "true");
      this.wrapper.addClass("idb-select--open");

      // open upwards when there is no room below the trigger
      var rect = this.trigger[0].getBoundingClientRect();
      var height = this.list.outerHeight();
      this.wrapper.toggleClass(
        "idb-select--up",
        rect.bottom + height > window.innerHeight && rect.top > height
      );

      this._activate(Math.max(this.select.selectedIndex, 0));
    },

    _close: function () {
      if (!this._isOpen()) {
        return;
      }
      this.list.prop("hidden", true);
      this.trigger.attr("aria-expanded", "false").removeAttr("aria-activedescendant");
      this.wrapper.removeClass("idb-select--open idb-select--up");
      this.options.removeClass("idb-select-option--active");
    },

    /* Highlights the option with the given index, as the keyboard focus. */
    _activate: function (index) {
      var option = this.options.eq(index);

      this.active = index;
      this.options.removeClass("idb-select-option--active");
      option.addClass("idb-select-option--active");
      this.trigger.attr("aria-activedescendant", option.attr("id"));
      option[0].scrollIntoView({ block: "nearest" });
    },

    _pick: function (index) {
      var changed = index !== this.select.selectedIndex;

      this.select.selectedIndex = index;
      this._render();
      this._close();
      this.trigger.trigger("focus");

      if (changed) {
        this.select.dispatchEvent(new Event("change", { bubbles: true }));
      }
    },

    _onTriggerClick: function () {
      if (this._isOpen()) {
        this._close();
      } else {
        this._open();
      }
    },

    _onOptionClick: function (event) {
      this._pick(this.options.index(event.currentTarget));
    },

    _onOptionHover: function (event) {
      this._activate(this.options.index(event.currentTarget));
    },

    _onKeydown: function (event) {
      var last = this.options.length - 1;

      if (!this._isOpen()) {
        if (["Enter", " ", "ArrowDown", "ArrowUp"].indexOf(event.key) !== -1) {
          event.preventDefault();
          this._open();
        }
        return;
      }

      switch (event.key) {
        case "ArrowDown":
          this._activate(Math.min(this.active + 1, last));
          break;
        case "ArrowUp":
          this._activate(Math.max(this.active - 1, 0));
          break;
        case "Home":
          this._activate(0);
          break;
        case "End":
          this._activate(last);
          break;
        case "Enter":
        case " ":
          this._pick(this.active);
          break;
        case "Escape":
          this._close();
          break;
        case "Tab":
          this._close();
          return;
        default:
          return;
      }
      event.preventDefault();
    },
  };
});
