/**
 * Mark the CKAN modules of the page load as initialized.
 *
 * After an htmx swap, CKAN initializes the modules of the swapped content
 * unless they have the `dm-initialized` attribute, which the page load
 * initialization doesn't set. A boosted request with `hx-swap="none"` (e.g. the
 * search form of the Datasets page) reports the whole body as the swapped
 * content, so every module of the page would be initialized again: the
 * advanced search would render its fields twice.
 */
jQuery(function () {
  document.querySelectorAll("[data-module]").forEach(function (node) {
    node.setAttribute("dm-initialized", true);
  });
});
