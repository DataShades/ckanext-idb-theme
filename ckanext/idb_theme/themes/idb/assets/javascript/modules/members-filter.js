/* Members filter
 * Filters the members table of the unit panel by the name or the role of a
 * member. Rows that do not match are hidden and a message is shown when
 * nothing is left.
 */
this.ckan.module('idb-members-filter', function ($) {
  return {
    options: {},

    initialize: function () {
      this.input = $('[data-members-search]', this.el);
      this.rows = $('[data-member]', this.el);
      this.empty = $('[data-members-empty]', this.el);

      this.input.on('input search', $.proxy(this._filter, this));
      this._filter();
    },

    teardown: function () {
      this.input.off('input search');
    },

    _filter: function () {
      var term = $.trim(this.input.val()).toLowerCase();
      var visible = 0;

      this.rows.each(function () {
        var row = $(this);
        var matches = !term || row.text().toLowerCase().indexOf(term) !== -1;

        row.toggle(matches);

        if (matches) {
          visible += 1;
        }
      });

      this.empty.toggleClass('d-none', visible !== 0);
    }
  };
});
