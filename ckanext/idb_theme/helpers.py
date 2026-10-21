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
    org_type = tk.h.default_group_type("organization")
    group_type = tk.h.default_group_type("group")

    return {
        "metrics": [
            {
                "value": tk.h.get_dataset_count(),
                "label": _("Available datasets"),
            },
            {
                "value": idb_theme_get_group_count(type="organization"),
                "label": tk.h.humanize_entity_type("organization", org_type, "facet label") or _("Organizations"),
            },
            {
                "value": "18+",
                "label": _("Countries covered"),
            },
            {
                "value": idb_theme_get_group_count(),
                "label": _("Thematic {entity_type}").format(
                    entity_type=tk.h.humanize_entity_type("group", group_type, "facet label") or _("Groups")
                ),
            },
        ],
    }


def idb_theme_get_group_count(type: str = "group") -> dict[str, int]:
    q = model.Session.query(model.Group).filter(model.Group.type == type).filter(model.Group.state == "active")
    if type == "organization":
        q = q.filter(model.Group.is_organization == True)
    elif type == "group":
        q = q.filter(model.Group.is_organization == False)
    else:
        raise ValueError(f"Invalid group type: {type}")  # noqa: TRY003
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


def idb_theme_download_count(pkg: dict[str, Any]) -> int:
    """Return the number of dataset downloads.

    The counter is provided by the ``iadb_iar_tracking`` plugin. Datasets
    without downloads show 0.
    """
    return pkg.get("num_downloads") or 0


def idb_theme_highlights_sort_options() -> list[dict[str, str]]:
    """Return the sort options of the Explore Highlights homepage section."""
    return [
        {"value": "data", "label": _("Most recent data")},
        {"value": "downloads", "label": _("Most downloaded")},
        {"value": "created", "label": _("Most recently added")},
        {"value": "modified", "label": _("Most recently updated")},
    ]


def idb_theme_highlights(sort: str | None = None) -> dict[str, Any]:
    """Get the top datasets of the whole catalog for the Explore Highlights section.

    Unknown sort option names fall back to the default one.
    """
    sorts = {
        "data": "temporal_end desc, temporal_start desc, metadata_modified desc",
        "downloads": "downloads_sort desc, metadata_modified desc",
        "created": "metadata_created desc",
        "modified": "metadata_modified desc",
    }

    if sort not in sorts:
        sort = "modified"

    result = tk.get_action("package_search")({}, {"rows": 30, "sort": sorts[sort]})
    packages = result["results"]

    # The indexed download counter is refreshed in batches, so it may lag
    # behind the live counters shown on the cards. Re-sort by the live ones;
    # the stable sort keeps the index order for ties.
    if sort == "downloads":
        packages.sort(key=lambda pkg: pkg.get("num_downloads") or 0, reverse=True)

    return {
        "sort": sort,
        "packages": packages,
    }


def idb_theme_dataset_card(pkg: dict[str, Any]) -> dict[str, Any]:
    """Collect the values displayed on the dataset card."""
    lang = tk.h.lang()

    gov_labels = _vocab_labels(pkg, "gov_tier", lang)
    tags = _fluent_values(pkg, "tags_translated", lang) or [t["display_name"] for t in pkg.get("tags", [])]

    start, end = _year(pkg.get("temporal_start")), _year(pkg.get("temporal_end"))

    return {
        "themes": _vocab_labels(pkg, "theme", lang),
        "units": _vocab_labels(pkg, "unitResponsible", lang),
        "countries": _vocab_labels(pkg, "spatial_coverage", lang),
        "coverage": [year for year in dict.fromkeys([start, end]) if year],
        "governance": gov_labels[0] if gov_labels else None,
        "tags": tags,
        "formats": tk.h.dict_list_reduce(pkg.get("resources", []), "format"),
        "published": _date(pkg.get("metadata_created")),
        "modified": _date(pkg.get("metadata_modified")),
        "downloads": idb_theme_download_count(pkg),
    }


def _fluent_values(pkg: dict[str, Any], field_name: str, lang: str) -> list[str]:
    """Get the list of values of a (fluent) multi-value field."""
    value = pkg.get(field_name)
    if isinstance(value, dict):
        value = value.get(lang) or value.get("en")
    if isinstance(value, str):
        value = [v.strip() for v in value.split(",") if v.strip()]
    return value or []


def _vocab_labels(pkg: dict[str, Any], field_name: str, lang: str) -> list[str]:
    """Resolve the localized labels of a controlled-vocabulary field."""
    value = _fluent_values(pkg, field_name, lang)
    if not value:
        return []

    choices = []
    schema = tk.h.scheming_get_dataset_schema(pkg.get("type") or "dataset")

    if schema:
        field = tk.h.scheming_field_by_name(schema["dataset_fields"], field_name)
        if field:
            choices = tk.h.scheming_field_choices(field) or []

    labels = {c["value"]: c.get("label", c["value"]) for c in choices}
    return [tk.h.scheming_language_text(labels.get(v, v), lang) for v in value]


def _year(value: Any) -> str:
    return str(value)[:4] if value else ""


def _date(value: str | None) -> str:
    if not value:
        return ""
    return tk.h.localised_nice_date(tk.h.date_str_to_datetime(value), show_date=True, format="d MMM y")


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
