this.ckan.module('slug-preview-target', {
  initialize: function () {
    var sandbox = this.sandbox;
    var options = this.options;
    var el = this.el;

    sandbox.subscribe('slug-preview-created', function (preview) {
      // Append the preview string after the target input.
      el.after(preview);
    });

    // Make sure there isn't a value in the field already...
    if (el.val() == '') {
      // Once the preview box is modified stop watching it.
      sandbox.subscribe('slug-preview-modified', function () {
        el.off('.slug-preview');
      });

      // Watch for updates to the target field and update the hidden slug field
      // triggering the "change" event manually.
      el.on('keyup.slug-preview input.slug-preview', function (event) {
        sandbox.publish('slug-target-changed', this.value);
        //slug.val(this.value).trigger('change');
      });
    }
  }
});

/* URL (slug) field shown as a preview bar under the name or title, with an
 * "Edit" button.
 *
 * Two states:
 *
 *   automatic - the URL field is hidden; the bar shows the label (e.g. "Data
 *               Project URL") and the address, updated from the name or title
 *               (slug-preview-target) while it's typed
 *   edit      - "Edit" hides the bar and shows the URL field; from then on the
 *               URL no longer follows the name
 *
 * A URL field with an error starts in the edit state.
 *
 * Options
 *
 *   prefix      - address before the slug, e.g. "example.org/dataset/"
 *   placeholder - shown while the slug is empty, e.g. "<dataset>"
 *   label       - label of the bar (default: "URL")
 */
this.ckan.module('slug-preview-slug', function ($) {
  return {
    options: {
      prefix: '',
      placeholder: '<slug>',
      label: ''
    },

    initialize: function () {
      $.proxyAll(this, /_on/);

      var sandbox = this.sandbox;
      var slug = this.el;
      var group = slug.closest('.form-group');

      if (!group.length) {
        return;
      }

      this.group = group;
      this.preview = this._buildPreview();

      // a field with an error stays visible, so the error can be fixed
      var invalid = slug.hasClass('is-invalid') || group.hasClass('error') || group.find('.error-inline, .invalid-feedback').length;
      if (!invalid) {
        group.hide();
        sandbox.publish('slug-preview-created', this.preview[0]);
        // without a target (no name field), the bar goes where the field was
        if (!$.contains(document, this.preview[0])) {
          group.after(this.preview);
        }
      }

      slug.on('change input', this._onSlugChange);
      // typing in the URL field stops it following the name
      slug.on('keypress', function (event) {
        if (event.charCode) {
          sandbox.publish('slug-preview-modified', this.preview[0]);
        }
      }.bind(this));

      sandbox.subscribe('slug-target-changed', function (value) {
        slug.val(value).trigger('change');
      });

      this._onSlugChange();
    },

    _buildPreview: function () {
      var label = this.options.label || this._('URL');
      var preview = $(
        '<div class="slug-preview" role="group">' +
          '<span class="slug-preview__icon" aria-hidden="true"><i class="fa fa-circle-info"></i></span>' +
          '<span class="slug-preview__text">' +
            '<span class="slug-preview__label"></span>' +
            '<span class="slug-preview__url"><span class="slug-preview__prefix"></span><span class="slug-preview__value"></span></span>' +
          '</span>' +
          '<button type="button" class="slug-preview__edit"></button>' +
        '</div>'
      );
      var labelId = 'slug-preview-label-' + Math.random().toString(36).slice(2, 8);

      preview.attr('aria-labelledby', labelId);
      preview.find('.slug-preview__label').attr('id', labelId).text(label);
      preview.find('.slug-preview__prefix').text(this.options.prefix);
      preview.find('.slug-preview__edit')
        .text(this._('Edit'))
        .attr('aria-label', this._('Edit') + ' ' + label)
        .attr('aria-controls', this.el.attr('id') || null)
        .on('click', this._onEdit);

      return preview;
    },

    _onSlugChange: function () {
      var value = this.el.val();
      this.preview.find('.slug-preview__value').text(value ? $.url.escape(value) : this.options.placeholder);
    },

    _onEdit: function (event) {
      event.preventDefault();
      this.preview.hide();
      this.group.show();
      this.sandbox.publish('slug-preview-modified', this.preview[0]);
      this.el.trigger('focus');
    }
  };
});
