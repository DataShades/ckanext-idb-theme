/*
 * Keeps a list of tags in a single row: shows as many tags as fit and
 * replaces the rest with a "+N" counter.
 *
 * The list must contain an item with the `data-overflow-counter` attribute,
 * which is used as the counter.
 *
 * Examples
 *
 * <ul class="d-flex flex-wrap" data-module="idb-tag-overflow">
 *   <li>Agriculture</li>
 *   <li>Education</li>
 *   <li class="d-none" data-overflow-counter></li>
 * </ul>
 *
 */
this.ckan.module("idb-tag-overflow", function ($) {
  "use strict";
  return {
    initialize: function () {
      this.counter = this.el.find("[data-overflow-counter]");
      this.tags = this.el.children().not(this.counter);
      this._update = this._update.bind(this);

      if ("ResizeObserver" in window) {
        this.observer = new ResizeObserver(this._update);
        this.observer.observe(this.el[0]);
      } else {
        $(window).on("resize", this._update);
      }

      this._update();
    },

    teardown: function () {
      if (this.observer) {
        this.observer.disconnect();
      } else {
        $(window).off("resize", this._update);
      }
    },

    /* Hides tags that wrap to the second row and shows how many are hidden. */
    _update: function () {
      // hiding tags changes only the height of the list, so recalculate only
      // when the width changes
      var width = this.el[0].clientWidth;
      if (width === this.width) {
        return;
      }
      this.width = width;

      var tags = this.tags.get();
      var counter = this.counter[0];

      tags.forEach(function (tag) {
        tag.classList.remove("d-none");
      });
      counter.classList.add("d-none");

      var top = tags[0].offsetTop;
      var visible = tags.filter(function (tag) {
        return tag.offsetTop === top;
      }).length;

      if (visible === tags.length) {
        return;
      }

      counter.classList.remove("d-none");

      // the counter itself must fit into the first row, so hide tags one by
      // one until it does
      for (;;) {
        tags.slice(visible).forEach(function (tag) {
          tag.classList.add("d-none");
        });
        counter.textContent = "+" + (tags.length - visible);

        if (visible === 0 || counter.offsetTop === top) {
          break;
        }
        visible--;
      }
    },
  };
});
