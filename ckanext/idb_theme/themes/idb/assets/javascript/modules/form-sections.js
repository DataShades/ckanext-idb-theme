/* Adds behaviour to the multi-section form components from
 * templates/macros/idb/form_layout.html. The module reads only data
 * attributes, so any entity form can use it.
 *
 * Markup it understands (anywhere inside the module element):
 *
 *   [data-form-section="<id>"]           collapsible section (ui.form_section)
 *   [data-form-field="<name>"]           field wrapper (ui.form_section_field)
 *     [data-form-field-required]         field counts toward completion
 *     [data-form-field-required-when]    ...while that field has one of [data-form-field-required-values]
 *     [data-form-field-also]             other inputs that must be filled as well
 *     a required mark (requiredSelector) also makes a field required; in a repeating
 *     row (rowSelector) with any value, the row's marked subfields are required
 *   [data-form-section-counter="<id>"]   text "{done}/{total}" for a section (data-template);
 *                                        gets .is-started when done > 0 and .is-complete when done == total
 *   [data-form-section-link="<id>"]      link that opens a section and scrolls to it
 *   [data-form-field-link="<name>"]      link that opens the field's section and scrolls to the field
 *   [data-form-progress-item="<name>"]   gets .is-complete when the field is filled
 *   [data-form-progress-bar]             overall progress bar
 *   [data-form-progress-summary]         text "{done} of {total}" (data-template)
 *   [data-form-next]                     button that stays disabled until all required fields are filled
 *   [data-form-sticky]                   sticky side block; gets `--form-sticky-top` so a block taller
 *                                        than the screen sticks by its bottom edge
 *
 * Options
 *
 *   primaryLang - for translated fields, only `<name>-<primaryLang>` is
 *                 required (default: "en")
 *
 * Example
 *
 *   <div data-module="form-sections" data-module-primary-lang="en">...</div>
 */
this.ckan.module('form-sections', function ($) {
  'use strict';

  var ERROR_SELECTOR = '.invalid-feedback, .error-block, .error-inline, .is-invalid';
  var SKIP_TYPES = ['hidden', 'button', 'submit', 'reset', 'image'];

  return {
    options: {
      primaryLang: 'en',
      // marks a required field; conditional fields add/remove it as their condition changes
      requiredSelector: '.control-required',
      // one row of a repeating field (ckanext-scheming repeating subfields)
      rowSelector: '.scheming-subfield-group'
    },

    initialize: function () {
      $.proxyAll(this, /_on/);

      this.root = this.el[0];
      this.sections = Array.prototype.slice.call(this.root.querySelectorAll('[data-form-section]'));
      this._scheduled = false;

      this.el.on('input change', this._onChange);
      this.el.on('click', '[data-form-section-link]', this._onSectionLinkClick);
      this.el.on('click', '[data-form-field-link]', this._onFieldLinkClick);

      this.root.addEventListener('show.bs.collapse', this._onSectionShow);
      this.root.addEventListener('hidden.bs.collapse', this._onSectionHidden);

      // other modules change what is required without input events: conditional
      // fields add/remove their required mark, repeating groups add/remove rows
      if (window.MutationObserver) {
        new MutationObserver(this._onChange).observe(this.root, {childList: true, subtree: true});
      }

      this._initSticky();
      this._openSectionsWithErrors();
      this._setActive(this._firstOpenSection());
      this._update();
    },

    /* Completion */

    _onChange: function () {
      // widgets and observers can fire many events in a row, so run the update once per frame
      if (this._scheduled) {
        return;
      }
      this._scheduled = true;
      window.requestAnimationFrame(function () {
        this._scheduled = false;
        this._update();
      }.bind(this));
    },

    _esc: function (value) {
      return window.CSS && window.CSS.escape ? window.CSS.escape(value) : value;
    },

    // Controls of a field: inputs named `name` or `name-<primary lang>`,
    // or any named control in `scope` when there are none.
    _controls: function (name, scope) {
      var primary = scope.querySelectorAll(
        '[name="' + this._esc(name) + '"], [name="' + this._esc(name + '-' + this.options.primaryLang) + '"]'
      );
      if (primary.length) {
        return Array.prototype.slice.call(primary);
      }
      return this._namedControls(scope);
    },

    _namedControls: function (scope) {
      return Array.prototype.slice.call(scope.querySelectorAll('[name]')).filter(function (el) {
        return SKIP_TYPES.indexOf((el.type || '').toLowerCase()) === -1;
      });
    },

    _hasValue: function (el) {
      if (el.disabled) {
        return false;
      }
      var type = (el.type || '').toLowerCase();
      if (type === 'checkbox' || type === 'radio') {
        return el.checked;
      }
      if (el.tagName === 'SELECT') {
        return Array.prototype.some.call(el.options, function (opt) {
          return opt.selected && opt.value !== '';
        });
      }
      return (el.value || '').trim() !== '';
    },

    _filled: function (name, scope) {
      return this._controls(name, scope).some(this._hasValue);
    },

    // Required marks that belong to `scope` itself, not to a nested repeating row.
    _ownMarks: function (scope) {
      var rowSelector = this.options.rowSelector;
      return Array.prototype.filter.call(scope.querySelectorAll(this.options.requiredSelector), function (mark) {
        var row = mark.closest(rowSelector);
        return !row || !scope.contains(row) || row === scope;
      });
    },

    // Rows of a repeating field with at least one value: their required subfields must be filled too.
    _activeRows: function (wrapper) {
      return Array.prototype.filter.call(wrapper.querySelectorAll(this.options.rowSelector), function (row) {
        return this._namedControls(row).some(this._hasValue);
      }, this);
    },

    _rowComplete: function (row) {
      return this._ownMarks(row).every(function (mark) {
        var label = mark.closest('label');
        var target = label && label.getAttribute('for');
        if (!target) {
          return true;
        }
        var name = target.replace(/^field-/, '');
        var group = label.closest('.form-group, .multilingual-field-group') || row;
        return this._controls(name, row).some(this._hasValue) || this._namedControls(group).some(this._hasValue);
      }, this);
    },

    // State of a field wrapper: is it required now, and is it complete?
    _fieldState: function (wrapper) {
      var name = wrapper.getAttribute('data-form-field');
      var rows = this._activeRows(wrapper);
      var required = wrapper.hasAttribute('data-form-field-required')
        || this._requiredByCondition(wrapper)
        || this._ownMarks(wrapper).length > 0;

      if (rows.length) {
        return {required: true, complete: rows.every(this._rowComplete, this)};
      }
      if (!required) {
        return {required: false, complete: false};
      }

      var complete = this._filled(name, wrapper);
      var also = (wrapper.getAttribute('data-form-field-also') || '').split(',').filter(Boolean);
      complete = complete && also.every(function (other) {
        return this._filled(other, wrapper);
      }, this);
      return {required: true, complete: complete};
    },

    // data-form-field-required-when: required while another field has one of the listed values
    _requiredByCondition: function (wrapper) {
      var controller = wrapper.getAttribute('data-form-field-required-when');
      if (!controller) {
        return false;
      }
      var values = (wrapper.getAttribute('data-form-field-required-values') || '').split(',');
      return this._controls(controller, this.root).some(function (el) {
        return !el.disabled && (el.value || '').split(',').some(function (value) {
          return value && values.indexOf(value) !== -1;
        });
      });
    },

    _update: function () {
      var done = 0;
      var total = 0;
      var perSection = {};

      this.sections.forEach(function (section) {
        perSection[section.getAttribute('data-form-section')] = {done: 0, total: 0};
      });

      Array.prototype.forEach.call(this.root.querySelectorAll('[data-form-field]'), function (wrapper) {
        var state = this._fieldState(wrapper);
        var name = wrapper.getAttribute('data-form-field');
        var section = wrapper.closest('[data-form-section]');
        var stats = section && perSection[section.getAttribute('data-form-section')];

        if (state.required) {
          total += 1;
          done += state.complete ? 1 : 0;
          if (stats) {
            stats.total += 1;
            stats.done += state.complete ? 1 : 0;
          }
        }

        wrapper.classList.toggle('is-complete', state.required && state.complete);
        this._each('[data-form-progress-item="' + name + '"]', function (item) {
          item.hidden = !state.required;
          item.classList.toggle('is-complete', state.complete);
          var label = item.querySelector('[data-form-progress-state]');
          if (label) {
            this._setText(label, label.getAttribute(state.complete ? 'data-done' : 'data-pending'));
          }
        });
      }, this);

      Object.keys(perSection).forEach(function (id) {
        var stats = perSection[id];
        var optional = stats.total === 0;
        var finished = !optional && stats.done === stats.total;
        this._each('[data-form-section-counter="' + id + '"]', function (counter) {
          this._setText(counter, optional
            ? counter.getAttribute('data-optional-label')
            : this._format(counter, stats.done, stats.total));
          counter.classList.toggle('is-optional', optional);
          counter.classList.toggle('is-started', stats.done > 0);
          counter.classList.toggle('is-complete', finished);
        });
        this._each('[data-form-section="' + id + '"]', function (section) {
          section.classList.toggle('is-complete', finished);
        });
      }, this);

      var allDone = done === total;

      this._each('[data-form-progress-bar]', function (bar) {
        bar.setAttribute('aria-valuenow', done);
        bar.setAttribute('aria-valuemax', total);
        var fill = bar.firstElementChild;
        if (fill) {
          fill.style.width = (total ? (done / total) * 100 : 100) + '%';
        }
      });
      this._each('[data-form-progress-summary]', function (summary) {
        this._setText(summary, this._format(summary, done, total));
      });
      this._each('[data-form-next]', function (button) {
        button.disabled = !allDone;
        button.setAttribute('aria-disabled', String(!allDone));
      });
    },

    // write text only when it changes, so the MutationObserver doesn't loop
    _setText: function (el, text) {
      if (el.textContent !== text) {
        el.textContent = text;
      }
    },

    _format: function (el, done, total) {
      var template = el.getAttribute('data-template') || '{done}/{total}';
      return template.replace('{done}', done).replace('{total}', total);
    },

    _each: function (selector, fn) {
      Array.prototype.forEach.call(this.root.querySelectorAll(selector), fn, this);
    },

    /* Sticky side block */

    _initSticky: function () {
      this.sticky = this.root.querySelector('[data-form-sticky]');
      if (!this.sticky) {
        return;
      }
      var update = this._updateStickyTop.bind(this);
      window.addEventListener('resize', update);
      if (window.ResizeObserver) {
        // the block grows when sections open/close or the progress list wraps
        new ResizeObserver(update).observe(this.sticky);
      }
      update();
    },

    _updateStickyTop: function () {
      var gap = 16;
      var overflow = window.innerHeight - this.sticky.offsetHeight - gap;
      // fits: stick to the top; taller: stick when the bottom edge reaches the screen bottom
      this.sticky.style.setProperty('--form-sticky-top', Math.min(gap, overflow) + 'px');
    },

    /* Navigation */

    _onSectionLinkClick: function (event) {
      event.preventDefault();
      var id = event.currentTarget.getAttribute('data-form-section-link');
      var section = this.root.querySelector('[data-form-section="' + id + '"]');
      if (section) {
        this._openAndScroll(section, section);
      }
    },

    _onFieldLinkClick: function (event) {
      event.preventDefault();
      var name = event.currentTarget.getAttribute('data-form-field-link');
      var field = this.root.querySelector('[data-form-field="' + name + '"]');
      if (!field) {
        return;
      }
      var section = field.closest('[data-form-section]');
      this._openAndScroll(section, field, function () {
        var control = this._controls(name, field).filter(function (el) { return !el.disabled; })[0];
        if (control && control.offsetParent !== null) {
          control.focus({preventScroll: true});
        }
      }.bind(this));
    },

    _openAndScroll: function (section, target, callback) {
      var scroll = function () {
        target.scrollIntoView({behavior: 'smooth', block: 'start'});
        if (callback) {
          callback();
        }
      };
      if (section) {
        this._setActive(section);
      }
      var body = section && section.querySelector('.collapse');
      if (!body || body.classList.contains('show')) {
        scroll();
        return;
      }
      body.addEventListener('shown.bs.collapse', scroll, {once: true});
      window.bootstrap.Collapse.getOrCreateInstance(body, {toggle: false}).show();
    },

    _onSectionShow: function (event) {
      var section = this._sectionOf(event.target);
      if (section) {
        section.classList.add('is-open');
        this._setActive(section);
      }
    },

    _onSectionHidden: function (event) {
      var section = this._sectionOf(event.target);
      if (!section) {
        return;
      }
      section.classList.remove('is-open');
      if (section === this.active) {
        this._setActive(this._firstOpenSection());
      }
    },

    _sectionOf: function (body) {
      // ignore collapse events from nested widgets
      var section = body.closest('[data-form-section]');
      return section && section.querySelector('.collapse') === body ? section : null;
    },

    _firstOpenSection: function () {
      return this.sections.filter(function (section) {
        return section.classList.contains('is-open');
      })[0] || null;
    },

    _setActive: function (section) {
      this.active = section;
      var id = section ? section.getAttribute('data-form-section') : null;
      this._each('[data-form-section-link]', function (link) {
        var active = link.getAttribute('data-form-section-link') === id;
        var item = link.closest('.form-section-nav__item') || link;
        item.classList.toggle('is-active', active);
        if (active) {
          link.setAttribute('aria-current', 'true');
        } else {
          link.removeAttribute('aria-current');
        }
      });
    },

    _openSectionsWithErrors: function () {
      this.sections.forEach(function (section) {
        var body = section.querySelector('.collapse');
        if (body && !body.classList.contains('show') && section.querySelector(ERROR_SELECTOR)) {
          body.classList.add('show');
          section.classList.add('is-open');
          var toggle = section.querySelector('[data-bs-toggle="collapse"]');
          if (toggle) {
            toggle.classList.remove('collapsed');
            toggle.setAttribute('aria-expanded', 'true');
          }
        }
      });
    }
  };
});
