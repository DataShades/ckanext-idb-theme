this.ckan.module('additional-info-linkify', function ($) {
  'use strict';

  var URL_REGEX = /https?:\/\/[^\s<>"']+/gi;

  return {
    options: {},

    initialize: function () {
      var self = this;
      $('td.dataset-details', this.el).each(function () {
        self._linkifyCell(this);
      });
    },

    _linkifyCell: function (cell) {
      var textNodes = this._collectTextNodes(cell);

      textNodes.forEach(function (textNode) {
        var text = textNode.nodeValue;
        if (!text || !URL_REGEX.test(text)) {
          URL_REGEX.lastIndex = 0;
          return;
        }
        URL_REGEX.lastIndex = 0;

        var fragment = document.createDocumentFragment();
        var lastIndex = 0;
        var match;

        while ((match = URL_REGEX.exec(text)) !== null) {
          if (match.index > lastIndex) {
            fragment.appendChild(
              document.createTextNode(text.slice(lastIndex, match.index))
            );
          }

          var url = match[0].replace(/[.,;:!?)]+$/, '');
          var trailing = match[0].slice(url.length);

          var link = document.createElement('a');
          link.href = url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.textContent = url;
          fragment.appendChild(link);

          if (trailing) {
            fragment.appendChild(document.createTextNode(trailing));
          }

          lastIndex = match.index + match[0].length;
        }

        if (lastIndex < text.length) {
          fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
        }

        textNode.parentNode.replaceChild(fragment, textNode);
      });
    },

    _collectTextNodes: function (cell) {
      var textNodes = [];
      var walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT);

      while (walker.nextNode()) {
        if (!this._isInsideLink(walker.currentNode, cell)) {
          textNodes.push(walker.currentNode);
        }
      }

      return textNodes;
    },

    _isInsideLink: function (node, cell) {
      var parent = node.parentElement;

      while (parent && parent !== cell) {
        if (parent.tagName === 'A') {
          return true;
        }
        parent = parent.parentElement;
      }

      return false;
    },
  };
});
