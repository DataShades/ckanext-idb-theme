from __future__ import annotations

from . import config


def idb_theme_default_collapsed(facet_name: str):
    """Check whether the facet with the given name should be collapsed by default."""
    return facet_name in config.collapsed_facets()
