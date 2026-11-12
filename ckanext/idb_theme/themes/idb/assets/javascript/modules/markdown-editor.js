/* Formatting toolbar and character counter of a Markdown textarea
 * (ui.markdown_editor in templates/macros/idb/form_layout.html).
 *
 * The toolbar wraps the selection in Markdown: **bold**, _italic_, "- " list
 * items and [text](url) links. The counter shows the length of the Markdown
 * source against the textarea's maxlength, which the browser enforces; the
 * toolbar never inserts text past it.
 *
 * Markup it understands (inside the module element):
 *
 *   textarea                          the edited field
 *   [data-markdown-format="<name>"]   toolbar button: bold, italic, list or link
 *   [data-markdown-counter]           counter text, from data-template ("{count}/{max} characters")
 */
this.ckan.module('markdown-editor', function ($) {
  'use strict';

  return {
    initialize: function () {
      $.proxyAll(this, /_on/);

      this.textarea = this.el.find('textarea')[0];
      this.counter = this.el.find('[data-markdown-counter]')[0];
      if (!this.textarea) {
        return;
      }

      this.el.find('[role="toolbar"]').prop('hidden', false);
      this.el.on('click', '[data-markdown-format]', this._onFormat);
      $(this.textarea).on('input change', this._onInput);
      this._updateCounter();
    },

    _onInput: function () {
      this._updateCounter();
    },

    _onFormat: function (event) {
      event.preventDefault();
      var format = event.currentTarget.getAttribute('data-markdown-format');
      var textarea = this.textarea;
      var start = textarea.selectionStart;
      var end = textarea.selectionEnd;
      var selected = textarea.value.slice(start, end);
      var result;

      if (format === 'bold') {
        result = this._wrap(selected || this._('bold text'), '**', '**');
      } else if (format === 'italic') {
        result = this._wrap(selected || this._('italic text'), '_', '_');
      } else if (format === 'list') {
        result = this._list(selected, start);
      } else if (format === 'link') {
        var url = window.prompt(event.currentTarget.getAttribute('data-link-prompt') || this._('Link URL'), 'https://');
        if (!url) {
          textarea.focus();
          return;
        }
        result = this._wrap(selected || this._('link text'), '[', '](' + url + ')');
      }

      if (result) {
        this._replace(start, end, result.text, result.selectStart, result.selectEnd);
      }
    },

    // `text` between the markers, with the text itself selected afterwards
    _wrap: function (text, before, after) {
      return {text: before + text + after, selectStart: before.length, selectEnd: before.length + text.length};
    },

    // every selected line becomes a list item, on a line of its own
    _list: function (selected, start) {
      var lines = (selected || this._('list item')).split('\n').map(function (line) {
        return /^\s*[-*] /.test(line) ? line : '- ' + line;
      });
      var prefix = start > 0 && this.textarea.value.charAt(start - 1) !== '\n' ? '\n' : '';
      var text = prefix + lines.join('\n');
      return {text: text, selectStart: text.length, selectEnd: text.length};
    },

    _replace: function (start, end, text, selectStart, selectEnd) {
      var textarea = this.textarea;
      var max = parseInt(textarea.getAttribute('maxlength'), 10);
      var length = textarea.value.length - (end - start) + text.length;

      textarea.focus();
      if (max && length > max) {
        return;
      }

      textarea.setRangeText(text, start, end, 'end');
      textarea.setSelectionRange(start + selectStart, start + selectEnd);
      // other modules (completion counters, previews) listen for input
      textarea.dispatchEvent(new Event('input', {bubbles: true}));
    },

    _updateCounter: function () {
      if (!this.counter) {
        return;
      }
      var template = this.counter.getAttribute('data-template') || '{count}/{max}';
      var max = this.counter.getAttribute('data-max');
      var text = template.replace('{count}', this.textarea.value.length).replace('{max}', max);
      if (this.counter.textContent !== text) {
        this.counter.textContent = text;
      }
    }
  };
});
