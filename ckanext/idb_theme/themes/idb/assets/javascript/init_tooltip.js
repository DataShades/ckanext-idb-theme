// Initialize tooltips using Bootstrap
$(function() {
    $('[data-bs-toggle="tooltip"]').each(function (index, element) {
        bootstrap.Tooltip.getOrCreateInstance(element)
    })
})

// Tooltips added after page load (repeating fields, htmx swaps) are created on first hover/focus
$(function() {
    new bootstrap.Tooltip(document.body, {selector: '[data-bs-toggle="tooltip"]'})
})
