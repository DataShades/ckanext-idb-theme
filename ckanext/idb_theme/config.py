from __future__ import annotations

import ckan.plugins.toolkit as tk

COLLAPSED_FACETS = "theme.idb.collapsed_facets"
HIDE_EMPTY_FOLLOWERS = "theme.idb.hide_empty_followers"
HOME_TITLE = "theme.idb.home_title"


def collapsed_facets() -> list[str]:
    """List of facet fields to be collapsed by default on the search results page."""
    return tk.config[COLLAPSED_FACETS]


def hide_empty_followers() -> bool:
    """Hide follower counters when an entity has no followers."""
    return tk.config[HIDE_EMPTY_FOLLOWERS]


def home_title() -> str:
    """Browser title for the portal homepage."""
    return tk.config.get(HOME_TITLE) or tk.config["ckan.site_title"]
