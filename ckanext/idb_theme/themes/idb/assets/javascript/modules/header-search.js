/* Search form that covers the header bar on narrow screens.
 *
 * The inline site search is hidden on narrow screens, so the search icon in
 * the header bar opens this form instead and focuses the field. Only the header
 * is covered - the rest of the page stays visible and scrollable. The form is
 * closed with the X button, the Escape key, on submit, or when the window grows
 * to the desktop layout.
 *
 * trigger - selector of the header action that opens the form
 * input   - selector of the field inside the form
 * close   - selector of the button that closes the form
 *
 */
this.ckan.module('idb-search-overlay', function (jQuery) {
  return {
    options: {
      trigger: '.header-search-toggle',
      input: '.header-search-overlay-input',
      close: '.header-search-overlay-close',
      navigation: '#main-navigation-toggle',
    },

    initialize: function () {
      this._overlay = this.el[0];
      this._trigger = document.querySelector(this.options.trigger);
      this._input = this._overlay.querySelector(this.options.input);
      this._close = this._overlay.querySelector(this.options.close);

      jQuery.proxyAll(this, /_on/);

      if (this._trigger) {
        this._trigger.addEventListener('click', this._onTriggerClick);
      }
      if (this._close) {
        this._close.addEventListener('click', this._onCloseClick);
      }
      this.el.on('keydown', this._onKeydown);
      this.el.on('submit', this._onSubmit);
      jQuery(window).on('resize', this._onResize);
    },

    teardown: function () {
      if (this._trigger) {
        this._trigger.removeEventListener('click', this._onTriggerClick);
      }
      if (this._close) {
        this._close.removeEventListener('click', this._onCloseClick);
      }
      this.el.off('keydown', this._onKeydown);
      this.el.off('submit', this._onSubmit);
      jQuery(window).off('resize', this._onResize);
    },

    open: function () {
      this._collapseNavigation();
      this._overlay.classList.add('show');
      if (this._trigger) {
        this._trigger.setAttribute('aria-expanded', 'true');
      }
      if (this._input) {
        this._input.focus();
      }
    },

    close: function () {
      this._overlay.classList.remove('show');
      if (this._trigger) {
        this._trigger.setAttribute('aria-expanded', 'false');
        this._trigger.focus();
      }
    },

    /* The form covers the whole header, so the collapsed navigation would be
     * hidden behind it; collapse it first to keep the header height stable. */
    _collapseNavigation: function () {
      var nav = document.querySelector(this.options.navigation);
      var Collapse = (window.bootstrap || {}).Collapse;

      if (nav && Collapse && nav.classList.contains('show')) {
        Collapse.getOrCreateInstance(nav, { toggle: false }).hide();
      }
    },

    _onTriggerClick: function (event) {
      event.preventDefault();
      this.open();
    },

    _onCloseClick: function (event) {
      event.preventDefault();
      this.close();
    },

    _onKeydown: function (event) {
      if (event.key === 'Escape' || event.key === 'Esc') {
        this.close();
      }
    },

    _onSubmit: function () {
      this.close();
    },

    _onResize: function () {
      // the desktop layout renders the inline field instead
      if (window.innerWidth >= 992) {
        this.close();
      }
    },
  };
});
