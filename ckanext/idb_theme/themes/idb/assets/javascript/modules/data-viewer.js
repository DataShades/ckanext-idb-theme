// data viewer module
// resizes the iframe when the content is loaded
this.ckan.module('data-viewer', function (jQuery) {
  return {
    options: {
      timeout: 200,
      minHeight: 400,
      padding: 30
    },

    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.on('load', this._onLoad);
      this._FirefoxFix();
      this.sandbox.subscribe('data-viewer-error', this._onDataViewerError);
      if (this.el.hasClass('data-explorer-frame')) {
        var frameDocument = this.el[0].contentDocument;
        if (frameDocument && frameDocument.readyState === 'complete') {
          this._onLoad();
        }
      }
    },

    _onDataViewerError: function(message) {
      var parent = this.el.parent();
      $('.data-viewer-error .collapse', parent).html(message);
      $('.data-viewer-error', parent).removeClass('js-hide');
       this.el.hide();
    },

    _onLoad: function() {
      var self = this;
      var isSameOrigin = false;
      try {
        isSameOrigin = new URL(this.el.attr('src'), window.location.href).origin === window.location.origin;
      } catch (error) {
        isSameOrigin = false;
      }
      if (isSameOrigin) {
        this._recalibrate();
        if (this.el.hasClass('data-explorer-frame')) {
          this._observeDataExplorer();
        }
        setTimeout(function() {
          self._recalibrate();
        }, this.options.timeout);
      } else {
        this.el.css('height', 600);
      }
    },

    _recalibrate: function() {
      if (this.el.hasClass('data-explorer-frame')) {
        var frameDocument = this.el.contents()[0];
        var wrapper = frameDocument && frameDocument.getElementById('resize_wrapper');
        if (wrapper) {
          var explorerHeight = Math.ceil(wrapper.getBoundingClientRect().height);
          if (explorerHeight > 0) {
            this.el.css('height', explorerHeight + 'px');
          }
        }
        return;
      }
      var height = this.el.contents().find('body').outerHeight(true);
      height = Math.max(height, this.options.minHeight);
      this.el.css('height', height + this.options.padding);
    },

    _observeDataExplorer: function() {
      var self = this;
      var frameDocument = this.el.contents()[0];
      var wrapper = frameDocument && frameDocument.getElementById('resize_wrapper');
      if (!wrapper || !window.ResizeObserver) {
        return;
      }
      if (this._explorerResizeObserver && this._explorerObservedWrapper === wrapper) {
        this._recalibrate();
        return;
      }
      if (this._explorerResizeObserver) {
        this._explorerResizeObserver.disconnect();
      }
      this._explorerResizeObserver = new window.ResizeObserver(function() {
        self._recalibrate();
      });
      this._explorerObservedWrapper = wrapper;
      this._explorerResizeObserver.observe(wrapper);
      this._recalibrate();
    },

    // firefox caches iframes so force it to get fresh content
    _FirefoxFix: function() {
      if(/#$/.test(this.el.src)) {
        this.el.src = this.el.src.substr(0, this.src.length - 1);
      } else {
        this.el.src = this.el.src + '#';
      }
    }
  };
});
