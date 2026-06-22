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
    return {
        'metrics': [
            {
                'value': tk.h.get_dataset_count(),
                'label': _('Available datasets'),
            },
            {
                'value': idb_theme_get_group_count(type='organization'),
                'label': _('Organizations'),
            },
            {
                'value': '18+',
                'label': _('Countries covered'),
            },
            {
                'value': idb_theme_get_group_count(),
                'label': _('Thematic groups'),
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

