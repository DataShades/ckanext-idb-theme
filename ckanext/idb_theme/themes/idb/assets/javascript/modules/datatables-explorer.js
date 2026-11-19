(function ($, window, document) {
  'use strict';

  if ($.fn.dataTable && $.fn.dataTable.defaults) {
    $.fn.dataTable.defaults.pagingType = 'full_numbers';
  }

  function translate(text) {
    return window.ckan && window.ckan.i18n && window.ckan.i18n._
      ? window.ckan.i18n._(text)
      : text;
  }

  // Seven icons adapted from Google's Material Symbols Outlined (Apache-2.0):
  // https://github.com/google/material-design-icons/tree/master/symbols/web
  // Embedded paths use currentColor to inherit toolbar states in every view.
  var toolbarIcons = {
    table: '<svg viewBox="0 -960 960 960" fill="currentColor" aria-hidden="true" focusable="false"><path d="M120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200q-33 0-56.5-23.5T120-200Zm80-400h560v-160H200v160Zm213 200h134v-120H413v120Zm0 200h134v-120H413v120ZM200-400h133v-120H200v120Zm427 0h133v-120H627v120ZM200-200h133v-120H200v120Zm427 0h133v-120H627v120Z"/></svg>',
    copy: '<svg viewBox="0 -960 960 960" fill="currentColor" aria-hidden="true" focusable="false"><path d="M760-200H320q-33 0-56.5-23.5T240-280v-560q0-33 23.5-56.5T320-920h280l240 240v400q0 33-23.5 56.5T760-200ZM560-640v-200H320v560h440v-360H560ZM160-40q-33 0-56.5-23.5T80-120v-560h80v560h440v80H160Zm160-800v200-200 560-560Z"/></svg>',
    visibility: '<svg viewBox="0 -960 960 960" fill="currentColor" aria-hidden="true" focusable="false"><path d="m644-428-58-58q9-47-27-88t-93-32l-58-58q17-8 34.5-12t37.5-4q75 0 127.5 52.5T660-500q0 20-4 37.5T644-428Zm128 126-58-56q38-29 67.5-63.5T832-500q-50-101-143.5-160.5T480-720q-29 0-57 4t-55 12l-62-62q41-17 84-25.5t90-8.5q151 0 269 83.5T920-500q-23 59-60.5 109.5T772-302Zm20 246L624-222q-35 11-70.5 16.5T480-200q-151 0-269-83.5T40-500q21-53 53-98.5t73-81.5L56-792l56-56 736 736-56 56ZM222-624q-29 26-53 57t-41 67q50 101 143.5 160.5T480-280q20 0 39-2.5t39-5.5l-36-38q-11 3-21 4.5t-21 1.5q-75 0-127.5-52.5T300-500q0-11 1.5-21t4.5-21l-84-82Zm319 93Zm-151 75Z"/></svg>',
    download: '<svg viewBox="0 -960 960 960" fill="currentColor" aria-hidden="true" focusable="false"><path d="M480-320 280-520l56-58 104 104v-326h80v326l104-104 56 58-200 200ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z"/></svg>',
    reset: '<svg viewBox="0 -960 960 960" fill="currentColor" aria-hidden="true" focusable="false"><path d="M280-120 80-320l200-200 57 56-104 104h607v80H233l104 104-57 56Zm400-320-57-56 104-104H120v-80h607L623-784l57-56 200 200-200 200Z"/></svg>',
    print: '<svg viewBox="0 -960 960 960" fill="currentColor" aria-hidden="true" focusable="false"><path d="M640-640v-120H320v120h-80v-200h480v200h-80Zm-480 80h640-640Zm560 100q17 0 28.5-11.5T760-500q0-17-11.5-28.5T720-540q-17 0-28.5 11.5T680-500q0 17 11.5 28.5T720-460Zm-80 260v-160H320v160h320Zm80 80H240v-160H80v-240q0-51 35-85.5t85-34.5h560q51 0 85.5 34.5T880-520v240H720v160Zm80-240v-160q0-17-11.5-28.5T760-560H200q-17 0-28.5 11.5T160-520v160h80v-80h480v80h80Z"/></svg>',
    share: '<svg viewBox="0 -960 960 960" fill="currentColor" aria-hidden="true" focusable="false"><path d="M280-360v-240q0-33 23.5-56.5T360-680h326L583-783l57-57 200 200-200 200-57-56 103-104H360v240h-80Zm-80 240q-33 0-56.5-23.5T120-200v-600h80v600h480v-160h80v160q0 33-23.5 56.5T680-120H200Z"/></svg>'
  };

  function setToolbarIcon(button, icon, label) {
    if (!button) {
      return;
    }
    if (button.jquery) {
      button = button[0];
    }
    if (!button) {
      return;
    }
    var title = button.getAttribute('title') || label;
    button.innerHTML = icon;
    button.setAttribute('aria-label', title);
    button.setAttribute('title', title);
  }

  function setToolbarIcons(dt) {
    var toggle = dt.button('viewToggleButton:name');
    if (toggle.any()) {
      toggle.text(toolbarIcons.table);
      setToolbarIcon(toggle.node(), toolbarIcons.table, translate('Table/List toggle'));
    }

    var selectors = [
      ['.buttons-copy', toolbarIcons.copy, translate('Copy to clipboard')],
      ['.buttons-colvis', toolbarIcons.visibility, translate('Toggle column visibility')],
      ['.buttons-collection:not(.buttons-colvis)', toolbarIcons.download, translate('Filtered download')],
      ['.buttons-print', toolbarIcons.print, translate('Print')]
    ];
    selectors.forEach(function (item) {
      var button = document.querySelector('.dt-buttons ' + item[0]);
      setToolbarIcon(button, item[1], item[2]);
    });
    var reset = dt.button('resetButton:name');
    if (reset.any()) {
      setToolbarIcon(reset.node(), toolbarIcons.reset, translate('Reset'));
    }
    var share = dt.button('shareButton:name');
    if (share.any()) {
      setToolbarIcon(share.node(), toolbarIcons.share, translate('Share current view'));
    }
  }

  $(document).on('init.dt', function (event, settings) {
    if (!settings.nTable || settings.nTable.id !== 'dtprv') {
      return;
    }

    var dt = new $.fn.dataTable.Api(settings);
    setToolbarIcons(dt);
    var searchInput = document.querySelector('#dtprv_filter input[type="search"]');
    var lengthLabel = document.querySelector('#dtprv_length label');

    if (searchInput) {
      searchInput.setAttribute('placeholder', translate('Search all columns…'));
      searchInput.setAttribute('aria-label', translate('Search all columns'));
    }

    if (lengthLabel) {
      var lengthSelect = lengthLabel.querySelector('select');
      Array.prototype.slice.call(lengthLabel.childNodes).forEach(function (node) {
        if (node.nodeType === 3) {
          lengthLabel.removeChild(node);
        }
      });
      if (lengthSelect) {
        lengthLabel.insertBefore(document.createTextNode(translate('Items per page') + ': '), lengthSelect);
      }
    }

    var footerControls = document.createElement('div');
    footerControls.className = 'dtprv-footer-controls';
    ['dtprv_length', 'dtprv_info', 'dtprv_paginate'].forEach(function (id) {
      var control = document.getElementById(id);
      if (control) {
        footerControls.appendChild(control);
      }
    });
    if (footerControls.childNodes.length) {
      document.querySelector('.dataTables_wrapper').appendChild(footerControls);
    }

    function updateFilterPlaceholders() {
      document.querySelectorAll('.dataTables_scrollHead thead tr:nth-child(2) th input.fhead').forEach(function (input) {
        if (input.placeholder) {
          return;
        }
        var header = input.closest('th');
        var visibleIndex = header ? header.cellIndex : -1;
        var column = visibleIndex >= 0 ? dt.column(visibleIndex + ':visible') : null;
        var label = column && column.any() ? column.name() : '';
        if (!label && header) {
          label = header.textContent.trim();
        }
        if (label) {
          input.setAttribute('placeholder', label);
        }
      });
    }
    updateFilterPlaceholders();

    function updateInfo() {
      var info = document.getElementById('dtprv_info');
      if (!info) {
        return;
      }
      var page = dt.page.info();
      var first = page.recordsDisplay ? page.start + 1 : 0;
      var range = translate('{start}–{end} of {total}')
        .replace('{start}', first)
        .replace('{end}', page.end)
        .replace('{total}', page.recordsDisplay);
      var filtered = Boolean(dt.search()) || dt.columns().search().toArray().some(Boolean);
      var response = dt.ajax.json();
      var estimated = response && response.total_was_estimated;
      info.textContent = range;
      if (filtered) {
        info.appendChild(document.createTextNode(' (' + translate('filtered') + ')'));
      }
      if (estimated) {
        info.appendChild(document.createTextNode(' (' + translate('estimated') + ')'));
      }
      var filterIcon = document.getElementById('filterinfoicon');
      if (filterIcon) {
        window.setTimeout(function () {
          filterIcon.style.visibility = filtered ? 'visible' : 'hidden';
        }, 0);
      }
    }

    dt.on('draw.dt', updateFilterPlaceholders);
    dt.on('draw.dt', updateInfo);
    dt.on('column-visibility.dt column-reorder.dt responsive-resize.dt', updateFilterPlaceholders);
    updateInfo();
  });
})(window.jQuery, window, document);
