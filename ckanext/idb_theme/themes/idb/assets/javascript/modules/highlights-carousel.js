/*
 * Bootstrap carousel that does not wrap around: the "previous" control is
 * disabled on the first slide and the "next" control on the last one.
 *
 * Examples
 *
 * <div id="carousel" class="carousel slide" data-bs-wrap="false" data-module="idb-highlights-carousel">
 *   <div class="carousel-inner">
 *     <div class="carousel-item active">...</div>
 *     <div class="carousel-item">...</div>
 *   </div>
 *   <button data-bs-target="#carousel" data-bs-slide="prev" disabled>Previous</button>
 *   <button data-bs-target="#carousel" data-bs-slide="next">Next</button>
 * </div>
 *
 */
this.ckan.module("idb-highlights-carousel", function ($) {
  "use strict";
  return {
    initialize: function () {
      this.items = this.el.find(".carousel-item");
      this.prev = this.el.find('[data-bs-slide="prev"]');
      this.next = this.el.find('[data-bs-slide="next"]');
      this._update = this._update.bind(this);

      this.carousel = bootstrap.Carousel.getOrCreateInstance(this.el[0]);
      this.el[0].addEventListener("slid.bs.carousel", this._update);

      this._update();
    },

    teardown: function () {
      this.el[0].removeEventListener("slid.bs.carousel", this._update);
      this.carousel.dispose();
    },

    /* Enables only the controls that lead to an existing slide. */
    _update: function () {
      var index = this.items.index(this.items.filter(".active"));

      this.prev.prop("disabled", index <= 0);
      this.next.prop("disabled", index >= this.items.length - 1);
    },
  };
});
