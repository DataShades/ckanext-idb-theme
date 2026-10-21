from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import _

from . import config

INFO_GRAPH_COUNTRY_FACET = "vocab_iadb_iar_spatial_coverage"
INFO_GRAPH_GOV_TIER_FACET = "vocab_iadb_iar_gov_tier"
INFO_GRAPH_INSTITUTIONAL_TIER = "Institutional"
HOME_THEME_FACET = "vocab_iadb_iar_theme"


def idb_theme_default_collapsed(facet_name: str):
    """Check whether the facet with the given name should be collapsed by default."""
    return facet_name in config.collapsed_facets()


def idb_theme_info_graph() -> dict[str, Any]:
    """Get the key numbers of the homepage hero.

    Every metric has a link to the list page with the matching items.
    """
    dataset_type = tk.h.default_package_type()
    group_type = tk.h.default_group_type("group")

    result = tk.get_action("package_search")(
        {"user": tk.current_user.name},
        {
            "rows": 0,
            "facet.field": [INFO_GRAPH_COUNTRY_FACET, INFO_GRAPH_GOV_TIER_FACET],
            "facet.limit": -1,
            "include_private": tk.config.get("ckan.search.default_include_private"),
        },
    )
    facets = result.get("search_facets", {})
    gov_tiers = {item["name"]: item["count"] for item in facets.get(INFO_GRAPH_GOV_TIER_FACET, {}).get("items", [])}

    return {
        "metrics": [
            {
                "value": result["count"],
                "label": _("Datasets available"),
                "url": tk.h.url_for(f"{dataset_type}.search"),
            },
            {
                "value": gov_tiers.get(INFO_GRAPH_INSTITUTIONAL_TIER, 0),
                "label": _("Institutional datasets"),
                "url": tk.h.url_for(
                    f"{dataset_type}.search",
                    **{INFO_GRAPH_GOV_TIER_FACET: INFO_GRAPH_INSTITUTIONAL_TIER},
                ),
            },
            {
                "value": len(facets.get(INFO_GRAPH_COUNTRY_FACET, {}).get("items", [])),
                "label": _("Countries covered"),
                # TODO: link the Countries page once it is implemented.
                "url": tk.h.url_for(f"{dataset_type}.search"),
            },
            {
                "value": idb_theme_get_group_count(),
                "label": _("Data projects"),
                "url": tk.h.url_for(f"{group_type}.index"),
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


def idb_theme_data_projects(limit: int = 4) -> dict[str, Any]:
    """Get the most downloaded Data Projects for the homepage.

    Only projects with a cover image are shown. Projects that contain
    institutional datasets are preferred; when there are not enough of them,
    other projects with a cover image fill the free places. The chosen
    projects are sorted by downloads, highest first.
    """
    group_type = tk.h.default_group_type("group")
    stats = _group_stats()

    def downloads(name: str) -> int:
        return stats.get(name, {}).get("downloads", 0)

    names = [
        name
        for (name,) in model.Session.query(model.Group.name)
        .filter(model.Group.type == group_type)
        .filter(model.Group.state == "active")
        .filter(model.Group.is_organization == False)  # noqa: E712
        .filter(model.Group.image_url.isnot(None))
        .filter(model.Group.image_url != "")
    ]
    names.sort(key=downloads, reverse=True)

    chosen = [name for name in names if stats.get(name, {}).get("institutional")][:limit]
    chosen += [name for name in names if name not in chosen][: limit - len(chosen)]
    chosen.sort(key=downloads, reverse=True)

    projects = []
    for name in chosen:
        try:
            group = tk.get_action("group_show")(
                {},
                {
                    "id": name,
                    "include_datasets": False,
                    "include_dataset_count": False,
                    "include_extras": False,
                    "include_users": False,
                    "include_groups": False,
                    "include_tags": False,
                    "include_followers": False,
                },
            )
        except (tk.ObjectNotFound, tk.NotAuthorized):
            continue

        projects.append(
            {
                "title": group["display_name"],
                "description": group.get("description") or "",
                "image": group.get("image_display_url"),
                "datasets": stats.get(name, {}).get("datasets", 0),
                "url": tk.h.url_for(f"{group_type}.read", id=group["name"]),
            }
        )

    return {
        "total": idb_theme_get_group_count(),
        "projects": projects,
        "url": tk.h.url_for(f"{group_type}.index"),
    }


def _group_stats() -> dict[str, dict[str, int]]:
    """Count the datasets, institutional datasets and downloads of every group.

    Only datasets the current user can see are counted.
    """
    stats: dict[str, dict[str, int]] = {}
    rows = tk.config.get("ckan.search.rows_max")
    start = 0

    while True:
        result = tk.get_action("package_search")(
            {"user": tk.current_user.name},
            {
                "fq": "groups:[* TO *]",
                "fl": ["id", "groups", INFO_GRAPH_GOV_TIER_FACET],
                "rows": rows,
                "start": start,
                "include_private": tk.config.get("ckan.search.default_include_private"),
            },
        )

        for pkg in result["results"]:
            institutional = INFO_GRAPH_INSTITUTIONAL_TIER in (pkg.get(INFO_GRAPH_GOV_TIER_FACET) or [])
            for name in pkg.get("groups") or []:
                group = stats.setdefault(name, {"datasets": 0, "institutional": 0, "downloads": 0})
                group["datasets"] += 1
                group["institutional"] += institutional
                group["downloads"] += idb_theme_download_count(pkg)

        start += rows
        if start >= result["count"]:
            return stats


def idb_theme_explore_themes(limit: int = 8) -> dict[str, Any]:
    """Get the themes with the most datasets for the homepage.

    Only datasets the current user can see are counted.
    """
    dataset_type = tk.h.default_package_type()
    lang = tk.h.lang()

    result = tk.get_action("package_search")(
        {"user": tk.current_user.name},
        {
            "rows": 0,
            "facet.field": [HOME_THEME_FACET],
            "facet.limit": -1,
            "include_private": tk.config.get("ckan.search.default_include_private"),
        },
    )
    items = result.get("search_facets", {}).get(HOME_THEME_FACET, {}).get("items", [])
    items = sorted(items, key=lambda item: (-item["count"], item["name"]))

    # the facet holds English labels: find the vocabulary choices by them, to
    # show the label in the current language and the icon named by the choice ID
    choices = {
        tk.h.scheming_language_text(choice.get("label", choice["value"]), "en"): choice
        for choice in _field_choices(dataset_type, "theme")
    }
    items = [item for item in items if item["name"] in choices]

    return {
        "total": len(items),
        "themes": [
            {
                "id": choices[item["name"]]["value"],
                "name": tk.h.scheming_language_text(choices[item["name"]].get("label", item["name"]), lang),
                "count": item["count"],
                "url": tk.h.url_for(f"{dataset_type}.search", **{HOME_THEME_FACET: item["name"]}),
            }
            for item in items[:limit]
        ],
        # TODO: link the Themes page once it is implemented.
        "url": tk.h.url_for(f"{dataset_type}.search"),
    }


def idb_theme_explore_countries() -> dict[str, Any]:
    """Get the number of countries covered by the datasets the user can see."""
    dataset_type = tk.h.default_package_type()

    result = tk.get_action("package_search")(
        {"user": tk.current_user.name},
        {
            "rows": 0,
            "facet.field": [INFO_GRAPH_COUNTRY_FACET],
            "facet.limit": -1,
            "include_private": tk.config.get("ckan.search.default_include_private"),
        },
    )

    return {
        "total": len(result.get("search_facets", {}).get(INFO_GRAPH_COUNTRY_FACET, {}).get("items", [])),
        # TODO: link the Countries page once it is implemented.
        "url": tk.h.url_for(f"{dataset_type}.search"),
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

    choices = _field_choices(pkg.get("type") or "dataset", field_name)
    labels = {c["value"]: c.get("label", c["value"]) for c in choices}
    return [tk.h.scheming_language_text(labels.get(v, v), lang) for v in value]


def _field_choices(dataset_type: str, field_name: str) -> list[dict[str, Any]]:
    """Get the choices of a dataset schema field."""
    schema = tk.h.scheming_get_dataset_schema(dataset_type)
    if not schema:
        return []

    field = tk.h.scheming_field_by_name(schema["dataset_fields"], field_name)
    if not field:
        return []

    return tk.h.scheming_field_choices(field) or []


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
            "title": _("DataHub"),
            "paragraphs": [
                _(
                    "The DataHub is the IDB's internal catalog for data used in analytical and knowledge work "
                    "across sectors and countries. It brings together datasets produced through operational "
                    "activities, technical cooperation, economic studies, and other sector work, as well as "
                    "external, proprietary, and institutionally acquired data. The catalog helps teams discover "
                    "available data and understand how it can be accessed."
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
