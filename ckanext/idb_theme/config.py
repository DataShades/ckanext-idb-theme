from __future__ import annotations

import ckan.plugins.toolkit as tk

COLLAPSED_FACETS = "theme.idb.collapsed_facets"


def collapsed_facets() -> list[str]:
    """List of facet fields to be collapsed by default on the search results page."""
    return tk.config[COLLAPSED_FACETS]
