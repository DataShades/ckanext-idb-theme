from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import _

from . import config


def idb_theme_default_collapsed(facet_name: str):
    """Check whether the facet with the given name should be collapsed by default."""
    return facet_name in config.collapsed_facets()


def idb_theme_info_graph() -> dict[str, Any]:
    """Get the info graph metrics for the homepage."""
    org_type = tk.h.default_group_type('organization')
    group_type = tk.h.default_group_type('group')

    return {
        'metrics': [
            {
                'value': tk.h.get_dataset_count(),
                'label': _('Available datasets'),
            },
            {
                'value': idb_theme_get_group_count(type='organization'),
                'label': tk.h.humanize_entity_type('organization', org_type, 'facet label') or _('Organizations'),
            },
            {
                'value': '18+',
                'label': _('Countries covered'),
            },
            {
                'value': idb_theme_get_group_count(),
                'label': _('Thematic {entity_type}').format(
                    entity_type=tk.h.humanize_entity_type('group', group_type, 'facet label') or _('Groups')
                ),
            },
        ],
    }


def idb_theme_get_group_count(type: str = 'group') -> dict[str, int]:
    q = model.Session.query(model.Group)\
        .filter(model.Group.type == type)\
        .filter(model.Group.state == 'active')
    if type == 'organization':
        q = q.filter(model.Group.is_organization == True)
    elif type == 'group':
        q = q.filter(model.Group.is_organization == False)
    else:
        raise ValueError(f'Invalid group type: {type}')  # noqa: TRY003
    return q.count()


def idb_theme_show_followers_count(num_followers: int) -> bool:
    """Check whether the sidebar follower count should be displayed."""
    return num_followers > 0 or not config.hide_empty_followers()


def idb_theme_home_title() -> str:
    """Return the configured browser title for the portal homepage."""
    return config.home_title()


def idb_theme_hide_user_image_upload() -> bool:
    """Check whether user image upload controls should be hidden."""
    return config.hide_user_image_upload()


def idb_theme_portal_text(section: str, lang: str | None = None) -> dict[str, Any]:
    """Return generic fallback copy for theme-level text blocks."""
    texts = {
        "organization": {
            "title": tk.h.humanize_entity_type("organization", "organization", "facet label") or _("Organizations"),
            "paragraphs": [
                _("Organizations are used to create, manage and publish datasets."),
            ],
        },
        "collection": {
            "title": tk.h.humanize_entity_type("group", "group", "facet label") or _("Groups"),
            "paragraphs": [
                _("Groups are used to create and manage collections of datasets."),
            ],
        },
        "home": {
            "title": _("Welcome to CKAN"),
            "paragraphs": [
                _(
                    "This is a nice introductory paragraph about CKAN or the site in general. "
                    "We don't have any copy to go here yet but soon we will"
                ),
            ],
        },
        "about": {
            "title": _("About"),
            "paragraphs": [
                _("CKAN is the world's leading open-source data portal platform."),
            ],
        },
    }

    return texts[section]
