from __future__ import annotations

import ckan.plugins.toolkit as tk

COLLAPSED_FACETS = "theme.idb.collapsed_facets"
HIDE_EMPTY_FOLLOWERS = "theme.idb.hide_empty_followers"


def collapsed_facets() -> list[str]:
    """List of facet fields to be collapsed by default on the search results page."""
    return tk.config[COLLAPSED_FACETS]


def hide_empty_followers() -> bool:
    """Hide follower counters when an entity has no followers."""
    return tk.config[HIDE_EMPTY_FOLLOWERS]
