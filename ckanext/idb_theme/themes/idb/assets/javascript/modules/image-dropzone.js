/* Drag and drop image upload (ui.image_dropzone in templates/macros/idb/form_layout.html).
 *
 * Works with CKAN's image fields: the file goes in the `image_upload` file
 * input, the current image stays in the `image_url` input and "Remove" sets
 * `clear_upload`. A dropped file is put into the file input, so the form
 * submits it as if it was chosen with the file dialog.
 *
 * The status row under the drop area ([data-image-dropzone-status]) has a
 * `data-state`:
 *
 *   uploading - the browser reads the chosen file and checks it's an image
 *   success   - the image is ready to be submitted (or is the current one)
 *   error     - the file is refused: another type, larger than `maxSize` MB,
 *               or not a readable image; the message can be dismissed
 *
 * Fires `image-dropzone:change` (bubbling) on the module element with
 * `detail.url`: an object URL of the chosen file, or "" when the image is
 * removed. Previews listen for it.
 *
 * Options
 *
 *   maxSize   - maximum file size, in MB (default: 5)
 *   accept    - accepted MIME types, comma separated
 *   typeError - message for a file of another type
 *   sizeError - message for a file that is too large
 *   readError - message for a file that is not a readable image
 */
this.ckan.module('image-dropzone', function ($) {
  'use strict';

  return {
    options: {
      maxSize: 5,
      accept: 'image/png,image/jpeg',
      typeError: '',
      sizeError: '',
      readError: ''
    },

    initialize: function () {
      $.proxyAll(this, /_on/);

      var root = this.el[0];
      this.area = root.querySelector('[data-image-dropzone-area]');
      this.input = root.querySelector('input[type="file"]');
      this.current = root.querySelector('.image-dropzone__current');
      this.clear = root.querySelector('[data-image-dropzone-clear]');
      this.status = root.querySelector('[data-image-dropzone-status]');
      this.statusText = root.querySelector('[data-image-dropzone-text]');
      this.objectUrl = null;
      this.loading = null;

      if (!this.area || !this.input || !this.status) {
        return;
      }

      this.input.addEventListener('change', this._onFileChange);
      this.area.addEventListener('dragenter', this._onDragOver);
      this.area.addEventListener('dragover', this._onDragOver);
      this.area.addEventListener('dragleave', this._onDragLeave);
      this.area.addEventListener('drop', this._onDrop);
      this.el.on('click', '[data-image-dropzone-remove]', this._onRemove);
      this.el.on('click', '[data-image-dropzone-dismiss]', this._onDismiss);
    },

    _onDragOver: function (event) {
      event.preventDefault();
      this.area.classList.add('is-dragover');
    },

    _onDragLeave: function (event) {
      if (!this.area.contains(event.relatedTarget)) {
        this.area.classList.remove('is-dragover');
      }
    },

    _onDrop: function (event) {
      event.preventDefault();
      this.area.classList.remove('is-dragover');
      var files = event.dataTransfer && event.dataTransfer.files;
      if (!files || !files.length) {
        return;
      }
      // a DataTransfer is the only way to set the files of an input
      var transfer = new DataTransfer();
      transfer.items.add(files[0]);
      this.input.files = transfer.files;
      this.input.dispatchEvent(new Event('change', {bubbles: true}));
    },

    _onFileChange: function () {
      var file = this.input.files && this.input.files[0];
      if (!file) {
        return;
      }

      var problem = this._validate(file);
      if (problem) {
        this._refuse(problem);
        return;
      }

      // decode the image before accepting it: a renamed or broken file is refused
      var url = URL.createObjectURL(file);
      var image = new Image();
      this.loading = image;
      this._setState('uploading', file.name);

      image.onload = function () {
        if (this.loading !== image) {
          URL.revokeObjectURL(url);
          return;
        }
        this.loading = null;
        this.clear.value = '';
        this._revoke();
        this.objectUrl = url;
        this._setState('success', file.name);
        this._notify(url);
        this._changed();
      }.bind(this);

      image.onerror = function () {
        URL.revokeObjectURL(url);
        if (this.loading === image) {
          this.loading = null;
          this._refuse(this.options.readError || this._('The file is not a valid image.'));
        }
      }.bind(this);

      image.src = url;
    },

    // the chosen file is dropped; the current image, if any, stays
    _refuse: function (message) {
      this.loading = null;
      this.input.value = '';
      this._revoke();
      this._notify('');
      this._setState('error', message);
      this._changed();
    },

    _onRemove: function (event) {
      event.preventDefault();
      this.loading = null;
      this.input.value = '';
      this.current.value = '';
      this.clear.value = 'true';
      this._revoke();
      this._setState('', '');
      this._notify('');
      this._changed();
      this.input.focus();
    },

    // back to the current image, if any
    _onDismiss: function (event) {
      event.preventDefault();
      var name = this.current.value.split('/').pop();
      this._setState(name ? 'success' : '', name);
      this.input.focus();
    },

    _validate: function (file) {
      var accepted = this.options.accept.split(',').map(function (type) { return type.trim(); });
      if (accepted.indexOf(file.type) === -1) {
        return this.options.typeError || this._('This file type is not accepted.');
      }
      if (file.size > this.options.maxSize * 1024 * 1024) {
        return this.options.sizeError || this._('This file is too large.');
      }
      return '';
    },

    _setState: function (state, text) {
      this.status.setAttribute('data-state', state);
      this.status.setAttribute('aria-busy', String(state === 'uploading'));
      this.status.hidden = !state;
      this.statusText.textContent = text;
      this.area.classList.toggle('is-invalid', state === 'error');
      this.el.toggleClass('has-image', state === 'success');
    },

    // the completion counters listen for input
    _changed: function () {
      this.input.dispatchEvent(new Event('input', {bubbles: true}));
    },

    _notify: function (url) {
      this.el[0].dispatchEvent(new CustomEvent('image-dropzone:change', {bubbles: true, detail: {url: url}}));
    },

    _revoke: function () {
      if (this.objectUrl) {
        URL.revokeObjectURL(this.objectUrl);
        this.objectUrl = null;
      }
    }
  };
});
