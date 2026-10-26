/*
 * Filters panel of the dataset search (package/snippets/search_facets.html).
 *
 * - "View all" expands a long list in place.
 * - The search field of a filter hides the values that don't match it.
 * - The "Filters" button opens the panel as a full-screen dialog on mobile.
 *
 * htmx swaps the whole panel out of band after every filter change, and the
 * CKAN modules of an out of band swap are not initialized again. So the
 * handlers are delegated to the document once, on the page load, and the
 * panel state is kept here and restored after a swap: the filters the user
 * opened or closed, the expanded long lists, the search terms of the filters
 * and the focused value. The tooltips of the swapped panel are created here
 * as well.
 *
 * Examples
 *
 * <div class="filters" id="search-facets" data-module="idb-search-facets">...</div>
 *
 */
this.ckan.module("idb-search-facets", function () {
  "use strict";

  var openFacets = new Set();
  var closedFacets = new Set();
  var expandedFacets = new Set();
  var searchTerms = new Map();
  var focusedValue = null;
  var listening = false;

  function sectionOf(node) {
    return node.closest(".facet-section[data-facet]");
  }

  function filterValues(section) {
    var input = section.querySelector(".facet-search-input");
    if (!input) {
      return;
    }

    var term = input.value.trim().toLowerCase();
    var matches = 0;

    section.querySelectorAll(".facet-item").forEach(function (item) {
      var match = !term || (item.dataset.facetLabel || "").includes(term);
      item.hidden = !match;
      matches += match ? 1 : 0;
    });

    section.classList.toggle("searching", !!term);

    var empty = section.querySelector(".facet-search-empty");
    if (empty) {
      empty.hidden = matches > 0;
    }
  }

  function setExpanded(section, expanded) {
    var button = section.querySelector(".facet-view-all");
    section.classList.toggle("expanded", expanded);
    if (button) {
      button.setAttribute("aria-expanded", String(expanded));
    }
  }

  // Every out of band swap of a search request calls it: only the sections
  // that htmx has just added are restored.
  function restore() {
    var restored = false;

    document.querySelectorAll(".facet-section[data-facet]:not([data-restored])").forEach(function (section) {
      var key = section.dataset.facet;
      section.dataset.restored = "true";
      restored = true;

      // the server opens the filters with selected values
      if (openFacets.has(key) || closedFacets.has(key)) {
        var open = openFacets.has(key);
        var toggle = section.querySelector(".facet-section-toggle");
        var body = section.querySelector(".facet-section-body");
        body.classList.toggle("show", open);
        toggle.classList.toggle("collapsed", !open);
        toggle.setAttribute("aria-expanded", String(open));
      }

      setExpanded(section, expandedFacets.has(key));

      var input = section.querySelector(".facet-search-input");
      if (input && searchTerms.has(key)) {
        input.value = searchTerms.get(key);
        filterValues(section);
      }

      section.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (node) {
        bootstrap.Tooltip.getOrCreateInstance(node);
      });
    });

    if (restored && focusedValue) {
      var selector = '.facet-section[data-facet="' + CSS.escape(focusedValue.facet) + '"] ' +
        '.facet-item[data-facet-label="' + CSS.escape(focusedValue.label) + '"] a';
      var link = document.querySelector(selector);
      if (link) {
        link.focus();
      }
      focusedValue = null;
    }
  }

  function onShown(event) {
    var section = sectionOf(event.target);
    if (section) {
      openFacets.add(section.dataset.facet);
      closedFacets.delete(section.dataset.facet);
    }
  }

  function onHidden(event) {
    var section = sectionOf(event.target);
    if (section) {
      openFacets.delete(section.dataset.facet);
      closedFacets.add(section.dataset.facet);
    }
  }

  function onInput(event) {
    if (!event.target.matches(".facet-search-input")) {
      return;
    }

    var section = sectionOf(event.target);
    searchTerms.set(section.dataset.facet, event.target.value);
    filterValues(section);
  }

  function onKeydown(event) {
    // Enter in the search field of a filter would submit nothing useful
    if (event.key === "Enter" && event.target.matches(".facet-search-input")) {
      event.preventDefault();
    }

    if (event.key === "Escape" && document.body.classList.contains("filters-modal")) {
      document.body.classList.remove("filters-modal");
      var button = document.querySelector(".show-filters");
      if (button) {
        button.focus();
      }
    }
  }

  function onClick(event) {
    var viewAll = event.target.closest(".facet-view-all");
    if (viewAll) {
      var section = sectionOf(viewAll);
      var expanded = !section.classList.contains("expanded");
      setExpanded(section, expanded);
      expanded ? expandedFacets.add(section.dataset.facet) : expandedFacets.delete(section.dataset.facet);
      return;
    }

    var value = event.target.closest(".facet-item a");
    if (value) {
      focusedValue = {
        facet: sectionOf(value).dataset.facet,
        label: value.parentElement.dataset.facetLabel,
      };
      return;
    }

    if (event.target.closest(".show-filters")) {
      document.body.classList.add("filters-modal");
      var close = document.querySelector("#search-facets .filters-close");
      if (close) {
        close.focus();
      }
      return;
    }

    if (event.target.closest(".hide-filters")) {
      document.body.classList.remove("filters-modal");
    }
  }

  return {
    initialize: function () {
      // the sections of the page load have nothing to restore
      this.el[0].querySelectorAll(".facet-section[data-facet]").forEach(function (section) {
        section.dataset.restored = "true";
      });

      // once per page, in case the module is initialized again
      if (listening) {
        return;
      }
      listening = true;

      document.addEventListener("shown.bs.collapse", onShown);
      document.addEventListener("hidden.bs.collapse", onHidden);
      document.addEventListener("input", onInput);
      document.addEventListener("keydown", onKeydown);
      document.addEventListener("click", onClick);
      document.addEventListener("htmx:afterSwap", restore);
      document.addEventListener("htmx:oobAfterSwap", restore);
    },
  };
});
