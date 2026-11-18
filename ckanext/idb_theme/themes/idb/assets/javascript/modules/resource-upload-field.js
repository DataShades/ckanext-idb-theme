this.ckan.module('resource-upload-field', function (jQuery) {
  return {
    initialize: function() {
      // looked up in the form of the field: it may be loaded after the page, e.g. in a modal
      var form = this.el.closest('form');
      var nameField = form.find('input[name="name"]');
      var urlField = this.$('#field-resource-url');
      var nameIsDirty = !!nameField.val();

      nameField.on('change', function() {
        nameIsDirty = true;
      });

      // Change input type to text if Upload is selected
      if (this.$('#resource-url-upload').prop('checked')) {
        urlField.attr('type', 'text');
      }

      // revert to URL for Link option
      this.$('#resource-link-button').on('click', function() {
        urlField.attr('type', 'url');
      });

      this.$('#field-resource-upload').on('change', function() {
        if (nameIsDirty) {
          return;
        }
        var file_name = jQuery(this).val().split(/^C:\\fakepath\\/).pop();

        // Internet Explorer 6-11 and Edge 20+
        var isIE = !!document.documentMode;
        var isEdge = !isIE && !!window.StyleMedia;
        // for IE/Edge when 'include filepath option' is enabled
        if (isIE || isEdge) {
          var fName = file_name.match(/[^\\\/]+$/);
          file_name = fName ? fName[0] : file_name;
        }

        nameField.val(file_name);
      });
    }
  };
});
