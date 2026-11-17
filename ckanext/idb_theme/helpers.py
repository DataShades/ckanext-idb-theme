from __future__ import annotations

import datetime
import math
import re
from typing import Any

from flask import has_request_context
from markupsafe import Markup, escape

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import _

from . import config

INFO_GRAPH_COUNTRY_FACET = "vocab_iadb_iar_spatial_coverage"
INFO_GRAPH_GOV_TIER_FACET = "vocab_iadb_iar_gov_tier"
INFO_GRAPH_INSTITUTIONAL_TIER = "Institutional"
HOME_THEME_FACET = "vocab_iadb_iar_theme"

# Sort options of the Explore Highlights section and the Datasets page
DATASET_SORTS = {
    "data": "temporal_end desc, temporal_start desc, metadata_modified desc",
    "downloads": "downloads_sort desc, metadata_modified desc",
    "created": "metadata_created desc",
    "modified": "metadata_modified desc",
}
DEFAULT_DATASET_SORT = "modified"
# Default of the Datasets page: without a search term every score is equal, so
# it falls back to the most recently updated first
DATASETS_PAGE_SORT = "score desc, metadata_modified desc"

# "Items per page" options of the Datasets page, the first one is the default.
# The parameter starts with "_", so the dataset search view does not treat it
# as a facet filter.
DATASETS_PER_PAGE_OPTIONS = [8, 16, 24, 48]
DATASETS_PER_PAGE_PARAM = "_per_page"

# Dataset resource list (HTMX panel on the dataset read page).
RESOURCE_LIMIT_OPTIONS = [4, 8, 12, 24]
DEFAULT_RESOURCE_LIMIT = RESOURCE_LIMIT_OPTIONS[0]
DEFAULT_RESOURCE_SORT = DEFAULT_DATASET_SORT
RESOURCE_SORT_PARAM = "sort"
RESOURCE_LIMIT_PARAM = "limit"
RESOURCE_OFFSET_PARAM = "offset"
RESOURCE_Q_PARAM = "q"

# Dataset change-history offcanvas (HTMX panel on the dataset read page).
ACTIVITY_LIMIT_OPTIONS = [9, 18, 27, 45]
DEFAULT_ACTIVITY_LIMIT = ACTIVITY_LIMIT_OPTIONS[0]
ACTIVITY_TYPE_PARAM = "activity_type"
ACTIVITY_LIMIT_PARAM = "limit"
ACTIVITY_OFFSET_PARAM = "offset"

# Solr fields of the advanced search dropdowns. The composite search plugin
# must treat them as keywords (`ckanext.composite_search.plugin.default.keyword_fields`).
ADVANCED_SEARCH_ORGANIZATION_FIELD = "organization"
ADVANCED_SEARCH_FORMAT_FIELD = "res_format"
ADVANCED_SEARCH_LICENSE_FIELD = "vocab_license"
ADVANCED_SEARCH_TAGS_FIELD = "extras_tags_translated"
# the option name has a typo in ckanext-resource-indexer itself
ADVANCED_SEARCH_ATTACHMENTS_FIELD_OPTION = "ckanext.resource_indexer.index_field"


def idb_theme_default_collapsed(facet_name: str):
    """Check whether the facet with the given name should be collapsed by default."""
    return facet_name in config.collapsed_facets()


def idb_theme_facet_details(facet_name: str) -> dict[str, Any]:
    """Get the details of a filter of the search facets panel.

    tooltip     - the text of the info icon next to the filter title.
    long        - only the first values are shown, with a "View all" link.
    view_all    - the "View all" link text, with the `{num}` placeholder.
    search      - the placeholder of the field that filters the values, or
                  an empty string when the filter has no search field.
    sort_by_name - the values are sorted by name instead of the count.
    """
    details: dict[str, dict[str, Any]] = {
        "vocab_iadb_iar_coverage": {
            "tooltip": _("Countries covered within the dataset, including the 26 IDB borrowing member countries."),
        },
        "vocab_iadb_iar_dataset_type": {
            "tooltip": _("The type of data asset, for example a dataset or a geospatial dataset."),
        },
        "vocab_iadb_iar_region": {
            "tooltip": _("The world regions covered by the dataset, based on its countries."),
            "sort_by_name": True,
        },
        "vocab_iadb_iar_spatial_coverage": {
            "tooltip": _("The countries covered by the dataset."),
            "long": True,
            "view_all": _("View all {num} countries"),
            "search": _("Search countries"),
            "sort_by_name": True,
        },
        "temporal_coverage": {
            "tooltip": _("Time period covered by the dataset, as defined by the years represented in the data."),
        },
        "vocab_iadb_iar_theme": {
            "tooltip": _("The main topics of the dataset."),
            "long": True,
            "view_all": _("View all {num} themes"),
            "search": _("Search themes"),
        },
        "tags": {
            "tooltip": _("Keywords or terms that describe the dataset’s content and subject matter."),
            "long": True,
            "view_all": _("View all {num} tags"),
            "search": _("Search tags"),
        },
        "groups": {
            "tooltip": _("Groups of related datasets with a shared initiative, project or methodology."),
            "long": True,
            "view_all": _("View all {num} Data Projects"),
        },
        "organization": {
            "tooltip": _("The IDB division or unit responsible for the dataset."),
        },
        "vocab_iadb_iar_gov_tier": {
            "tooltip": _("The governance and documentation requirements that apply to the dataset."),
        },
        "res_format": {
            "tooltip": _("The file formats of the dataset’s resources, (e.g., CSV, PDF, or DTA)"),
        },
        "vocab_iadb_iar_admin_level": {
            "tooltip": _(
                "Level of geographic detail represented in the dataset (e.g., national, province, municipality)."
            ),
            "sort_by_name": True,
        },
    }

    return {
        "tooltip": "",
        "long": False,
        "view_all": _("View all {num}"),
        "search": "",
        "sort_by_name": False,
        **details.get(facet_name, {}),
    }


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
                # a portal with a page of all countries links it by chaining the helper
                "url": tk.h.url_for(f"{dataset_type}.search"),
            },
            {
                "value": idb_theme_get_group_count(),
                "label": _("Data projects"),
                "url": tk.h.url_for(f"{group_type}.index"),
            },
        ],
    }


def idb_theme_get_group_count(type: str = "group") -> int:
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


def idb_theme_group_members(group_id: str) -> list[dict[str, Any]]:
    """Return the members of a group or organization.

    The list feeds the "Members" panel of the group page.

    :param group_id: id or name of the group
    :type group_id: string

    :returns: list of dicts with the ``id``, ``name``, ``display_name``,
        ``initials``, ``image_url`` and ``role`` keys
    :rtype: list
    """
    try:
        members = tk.get_action("member_list")(
            {"user": tk.current_user.name},
            {"id": group_id, "object_type": "user"},
        )
    except (tk.ObjectNotFound, tk.NotAuthorized):
        return []

    result = []
    for user_id, name, role in members:
        user = model.User.get(user_id)
        display_name = (user.display_name or user.name) if user else name
        result.append(
            {
                "id": user_id,
                "name": name,
                "display_name": display_name,
                "initials": _initials(display_name),
                "image_url": user.image_url if user else None,
                "role": role,
            }
        )

    return result


def _initials(name: str) -> str:
    """Return the initials shown instead of the image of a user."""
    words = name.split() or [name]

    if len(words) > 1:
        return (words[0][:1] + words[1][:1]).upper()

    return words[0][:2].upper()


def idb_theme_home_title() -> str:
    """Return the configured browser title for the portal homepage."""
    return config.home_title()


def idb_theme_hide_user_image_upload() -> bool:
    """Check whether user image upload controls should be hidden."""
    return config.hide_user_image_upload()


def idb_theme_current_year() -> int:
    """Return the current year for the footer copyright notice."""
    return datetime.datetime.now(tz=datetime.timezone.utc).date().year


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
    if sort not in DATASET_SORTS:
        sort = DEFAULT_DATASET_SORT

    result = tk.get_action("package_search")({}, {"rows": 30, "sort": DATASET_SORTS[sort]})
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


def idb_theme_dataset_sort_options() -> list[dict[str, str]]:
    """Return the "Order by" options of the Datasets page.

    The values are Solr sort expressions: the dataset search view passes the
    ``sort`` parameter to ``package_search`` as is.
    """
    return [
        {"value": DATASETS_PAGE_SORT, "label": _("Relevance")},
        *(
            {"value": DATASET_SORTS[option["value"]], "label": option["label"]}
            for option in idb_theme_highlights_sort_options()
        ),
    ]


def idb_theme_datasets_per_page(options: list[int] | None = None) -> int:
    """Return the number of datasets per page chosen on the Datasets page.

    ``options`` are the page sizes of the dropdown, the ones of the Datasets
    page by default; other pages, e.g. the Data Projects page of
    ckanext-iadb-iar, set their own. A missing or unknown value falls back to
    the first option, the one the dropdown shows selected.
    """
    options = options or DATASETS_PER_PAGE_OPTIONS
    value = tk.request.args.get(DATASETS_PER_PAGE_PARAM, type=int) if has_request_context() else None

    return value if value in options else options[0]


def idb_theme_datasets_pagination(item_count: int, options: list[int] | None = None) -> dict[str, Any]:
    """Get the pagination of the Datasets page.

    The page size is chosen by the user, while the ``Page`` object of the
    dataset search view is built with ``ckan.datasets_per_page``, so the
    numbers are computed here from the request. ``options`` are the page
    sizes of the dropdown, see `idb_theme_datasets_per_page`.
    """
    options = options or DATASETS_PER_PAGE_OPTIONS
    per_page = idb_theme_datasets_per_page(options)
    page = tk.h.get_page_number(tk.request.args)
    last_page = max(math.ceil(item_count / per_page), 1)

    def url(number: int) -> str:
        return tk.h.add_url_param(new_params={"page": number})

    return {
        "param": DATASETS_PER_PAGE_PARAM,
        "per_page": per_page,
        "per_page_options": options,
        "item_count": item_count,
        "first_item": min((page - 1) * per_page + 1, item_count),
        "last_item": min(page * per_page, item_count),
        "first_url": url(1) if page > 1 else None,
        "previous_url": url(min(page, last_page + 1) - 1) if page > 1 else None,
        "next_url": url(page + 1) if page < last_page else None,
        "last_url": url(last_page) if page < last_page else None,
    }


def idb_theme_resource_sort_options() -> list[dict[str, str]]:
    """Return the sort options of the dataset resources HTMX panel.

    Reuses the Explore Highlights / Datasets labels and option names, applied
    to resources of the current dataset.
    """
    return idb_theme_highlights_sort_options()


def idb_theme_activity_type_options() -> list[dict[str, str]]:
    """Return activity-type filter options for the change-history panel."""
    try:
        from ckanext.activity.logic.validators import VALIDATORS_PACKAGE_ACTIVITY_TYPES
    except ImportError:
        return []

    return [
        {"value": activity_type, "label": activity_type.replace("_", " ").title()}
        for activity_type in VALIDATORS_PACKAGE_ACTIVITY_TYPES
    ]


def idb_theme_user_initials(user_ref: str | None) -> str:
    """Return up to two initials for a user avatar.

    Prefers ``fullname`` (first letter of the first and last words). Falls back
    to the first two characters of ``name`` when fullname is empty.
    """
    if not user_ref:
        return "?"

    user = model.User.get(user_ref)
    if not user:
        return str(user_ref)[:2].upper() or "?"

    fullname = (user.fullname or "").strip()
    if fullname:
        words = [word for word in re.split(r"[\s,]+", fullname) if word]
        if len(words) == 1:
            return words[0][:2].upper()
        return f"{words[0][0]}{words[-1][0]}".upper()

    name = (user.name or "").strip()
    if name:
        return name[:2].upper()
    return "?"


def idb_theme_activity_item_html(item_html: str | Markup, initials: str) -> Markup:
    """Swap the CKAN fa-stack icon for a blue initials avatar.

    Leaves the avatar as its own sibling and wraps the remaining ``<li>``
    content in ``.change-history-body`` so the row can use flex centering
    instead of absolute positioning.

    Works on a plain string so Markup-aware ``replace`` cannot escape the
    injected HTML (that was breaking the change-history list).
    """
    avatar = (
        f'<span class="change-history-avatar" aria-hidden="true">'
        f"{escape(initials)}</span>"
    )
    text = re.sub(
        r'<span class="fa-stack fa-lg">.*?</span>\s*',
        avatar,
        str(item_html),
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        r'(<span class="change-history-avatar"[^>]*>.*?</span>)(.*?)(</li>\s*)$',
        r'\1<span class="change-history-body">\2</span>\3',
        text,
        count=1,
        flags=re.DOTALL,
    )
    return Markup(text)


def idb_theme_package_activity(
    pkg: dict[str, Any],
    activity_type: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any]:
    """Return a filtered, offset/limit page of package activities for the offcanvas panel.

    Unknown limit values fall back to the default (9). ``offset`` is snapped
    down to the start of the last page when it would land past the end.
    """
    type_values = {option["value"] for option in idb_theme_activity_type_options()}
    if has_request_context():
        if activity_type is None:
            activity_type = tk.request.args.get(ACTIVITY_TYPE_PARAM)
        if limit is None:
            limit = tk.request.args.get(ACTIVITY_LIMIT_PARAM, type=int)
        if offset is None:
            offset = tk.request.args.get(ACTIVITY_OFFSET_PARAM, type=int)

    if activity_type not in type_values:
        activity_type = ""
    if limit not in ACTIVITY_LIMIT_OPTIONS:
        limit = DEFAULT_ACTIVITY_LIMIT
    offset = max(offset or 0, 0)

    pkg_id = pkg.get("id") or ""
    pkg_name = pkg.get("name") or pkg_id
    activities: list[dict[str, Any]] = []
    item_count = 0

    if pkg_id and p.plugin_loaded("activity"):
        context: dict[str, Any] = {"user": tk.current_user.name, "auth_user_obj": tk.current_user}
        data_dict: dict[str, Any] = {"id": pkg_id, "limit": limit, "offset": offset}
        if activity_type:
            data_dict["activity_types"] = [activity_type]
        try:
            activities = tk.get_action("package_activity_list")(context, data_dict)
            item_count = _package_activity_count(pkg_id, activity_type or None)
        except (tk.ObjectNotFound, tk.NotAuthorized, tk.ValidationError):
            activities = []
            item_count = 0

    if item_count and offset >= item_count:
        offset = ((item_count - 1) // limit) * limit
        if pkg_id and p.plugin_loaded("activity"):
            context = {"user": tk.current_user.name, "auth_user_obj": tk.current_user}
            data_dict = {"id": pkg_id, "limit": limit, "offset": offset}
            if activity_type:
                data_dict["activity_types"] = [activity_type]
            try:
                activities = tk.get_action("package_activity_list")(context, data_dict)
            except (tk.ObjectNotFound, tk.NotAuthorized, tk.ValidationError):
                activities = []

    last_offset = ((item_count - 1) // limit) * limit if item_count else 0

    def page_url(next_offset: int) -> str:
        params: dict[str, Any] = {
            "id": pkg_name,
            "limit": limit,
            "offset": next_offset,
        }
        if activity_type:
            params["activity_type"] = activity_type
        return tk.h.url_for("idb_theme.package_activity", **params)

    return {
        "activity_type": activity_type,
        "activity_type_param": ACTIVITY_TYPE_PARAM,
        "limit": limit,
        "limit_param": ACTIVITY_LIMIT_PARAM,
        "limit_options": ACTIVITY_LIMIT_OPTIONS,
        "offset": offset,
        "offset_param": ACTIVITY_OFFSET_PARAM,
        "item_count": item_count,
        "activities": activities,
        "first_item": min(offset + 1, item_count) if item_count else 0,
        "last_item": min(offset + limit, item_count),
        "endpoint": tk.h.url_for("idb_theme.package_activity", id=pkg_name),
        "first_url": page_url(0) if offset > 0 else None,
        "previous_url": page_url(max(offset - limit, 0)) if offset > 0 else None,
        "next_url": page_url(offset + limit) if offset + limit < item_count else None,
        "last_url": page_url(last_offset) if offset < last_offset else None,
    }


def idb_theme_package_resources(
    pkg: dict[str, Any],
    sort: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    """Return a filtered, sorted, offset/limit page of resources for the dataset read panel.

    Unknown sort/limit values fall back to the defaults. ``offset`` is snapped
    down to the start of the last page when it would land past the end.
    """
    sort_values = {option["value"] for option in idb_theme_resource_sort_options()}
    if has_request_context():
        if sort is None:
            sort = tk.request.args.get(RESOURCE_SORT_PARAM)
        if limit is None:
            limit = tk.request.args.get(RESOURCE_LIMIT_PARAM, type=int)
        if offset is None:
            offset = tk.request.args.get(RESOURCE_OFFSET_PARAM, type=int)
        if q is None:
            q = tk.request.args.get(RESOURCE_Q_PARAM)

    if sort not in sort_values:
        sort = DEFAULT_RESOURCE_SORT
    if limit not in RESOURCE_LIMIT_OPTIONS:
        limit = DEFAULT_RESOURCE_LIMIT
    offset = max(offset or 0, 0)
    q = (q or "").strip()

    resources = _attach_resource_download_counts(
        _filter_package_resources(pkg.get("resources") or [], q),
        pkg.get("id"),
    )
    resources = _sorted_package_resources(resources, sort)
    item_count = len(resources)
    if item_count and offset >= item_count:
        offset = ((item_count - 1) // limit) * limit

    page_resources = resources[offset : offset + limit]
    last_offset = ((item_count - 1) // limit) * limit if item_count else 0
    pkg_id = pkg.get("name") or pkg.get("id")

    def page_url(next_offset: int) -> str:
        params: dict[str, Any] = {
            "id": pkg_id,
            "sort": sort,
            "limit": limit,
            "offset": next_offset,
        }
        if q:
            params["q"] = q
        return tk.h.url_for("idb_theme.package_resources", **params)

    return {
        "sort": sort,
        "sort_param": RESOURCE_SORT_PARAM,
        "limit": limit,
        "limit_param": RESOURCE_LIMIT_PARAM,
        "limit_options": RESOURCE_LIMIT_OPTIONS,
        "offset": offset,
        "offset_param": RESOURCE_OFFSET_PARAM,
        "q": q,
        "q_param": RESOURCE_Q_PARAM,
        "item_count": item_count,
        "resources": page_resources,
        "first_item": min(offset + 1, item_count) if item_count else 0,
        "last_item": min(offset + limit, item_count),
        "endpoint": tk.h.url_for("idb_theme.package_resources", id=pkg_id),
        "first_url": page_url(0) if offset > 0 else None,
        "previous_url": page_url(max(offset - limit, 0)) if offset > 0 else None,
        "next_url": page_url(offset + limit) if offset + limit < item_count else None,
        "last_url": page_url(last_offset) if offset < last_offset else None,
    }


def idb_theme_resource_card(pkg: dict[str, Any], resource: dict[str, Any]) -> dict[str, Any]:
    """Collect the values displayed on a dataset resource card."""
    title = tk.h.get_translated(resource, "name") or resource.get("name") or resource.get("id")
    description = tk.h.get_translated(resource, "description") or resource.get("description") or ""
    fmt = (resource.get("format") or "").strip()
    start, end = _year(resource.get("temporal_start")), _year(resource.get("temporal_end"))
    coverage = [year for year in dict.fromkeys([start, end]) if year]
    size_bytes = resource.get("byteSize") if resource.get("byteSize") not in (None, "") else resource.get("size")
    size_label = None
    try:
        if size_bytes not in (None, ""):
            size_label = tk.h.localised_filesize(int(size_bytes))
    except (TypeError, ValueError):
        size_label = None

    preview_url = tk.h.url_for(
        f"{pkg['type']}_resource.read",
        id=pkg["name"],
        resource_id=resource["id"],
    )
    download_url = _resource_download_url(pkg, resource)
    downloads = resource.get("num_downloads")
    if downloads is None:
        stamped = _attach_resource_download_counts([resource], pkg.get("id"))
        downloads = stamped[0].get("num_downloads") if stamped else 0

    return {
        "title": title,
        "description": description,
        "format": fmt.upper() if fmt else None,
        "coverage": coverage,
        "coverage_label": (
            _("{period} (Coverage)").format(period=" - ".join(coverage)) if coverage else None
        ),
        "downloads": downloads or 0,
        "size": size_label,
        "preview_url": preview_url,
        "download_url": download_url,
        "format_tip": _resource_format_tip(fmt),
        "created": resource.get("created"),
        "last_modified": resource.get("last_modified") or resource.get("metadata_modified"),
        "id": resource.get("id"),
    }


def idb_theme_sibling_resources(pkg: dict[str, Any], current_resource_id: str | None = None) -> dict[str, Any]:
    """Return other resources of the dataset for the resource-page sidebar.

    Excludes ``current_resource_id``. ``total`` is the full resource count of
    the dataset (including the current one).
    """
    resources = pkg.get("resources") or []
    stamped = _attach_resource_download_counts(resources, pkg.get("id"))
    siblings = [
        idb_theme_resource_card(pkg, resource)
        for resource in stamped
        if resource.get("id") != current_resource_id
    ]
    return {
        "total": len(resources),
        "resources": siblings,
    }


def _resource_download_url(pkg: dict[str, Any], resource: dict[str, Any]) -> str | None:
    """Return the download or external URL for a resource."""
    if resource.get("url_type") == "upload":
        filename = (resource.get("url") or "").rsplit("/", 1)[-1] or None
        return tk.h.url_for(
            f"{pkg['type']}_resource.download",
            id=pkg["name"],
            resource_id=resource["id"],
            filename=filename,
        )

    url = resource.get("url")
    return url if url and tk.h.is_url(url) else None


def _resource_format_tip(fmt: str) -> str | None:
    """Hint text shown under a resource card for known formats."""
    key = (fmt or "").strip().upper()
    tips = {
        # Data files
        "CSV": _(
            "CSV file. Opens in Excel, Google Sheets, R, Python (pandas) or any statistical software."
        ),
        "XLSX": _("Excel file. Opens in Excel, Google Sheets or LibreOffice."),
        "XLS": _("Excel file. Opens in Excel, Google Sheets or LibreOffice."),
        "XLSM": _("Excel file with macros. Opens in Excel. Macros may need to be enabled."),
        "DTA": _("Stata file. Opens in Stata, R (haven) or Python (pandas)."),
        "SAV": _("SPSS file. Opens in SPSS, R (haven) or Python (pandas)."),
        "JSON": _("JSON file. For developers. Opens in a text editor or any programming language."),
        "XML": _("XML file. For developers. Opens in a text editor or any programming language."),
        # Code files
        "DO": _("Stata script. Opens in Stata or any text editor."),
        "R": _("R script. Opens in R, RStudio or any text editor."),
        "PY": _("Python script. Opens in Python or any text editor."),
        # Documents
        "PDF": _("PDF document. Opens in any PDF reader or web browser."),
        "DOCX": _("Word document. Opens in Word, Google Docs or LibreOffice."),
        "DOC": _("Word document. Opens in Word, Google Docs or LibreOffice."),
        "PPT": _("PowerPoint presentation. Opens in PowerPoint, Google Slides or LibreOffice."),
        "PPTX": _("PowerPoint presentation. Opens in PowerPoint, Google Slides or LibreOffice."),
        "HTML": _("Web page. Opens in any web browser."),
        # Images
        "PNG": _("Image file. Opens in any image viewer or web browser."),
        "JPEG": _("Image file. Opens in any image viewer or web browser."),
        "JPG": _("Image file. Opens in any image viewer or web browser."),
        "GIF": _("Image file. Opens in any image viewer or web browser."),
        "BMP": _("Image file. Opens in any image viewer or web browser."),
        # Archives
        "ZIP": _("ZIP archive. Unzip it to see the files inside."),
        "RAR": _("RAR archive. Unzip it with a tool such as 7-Zip or WinRAR."),
        "GZ": _("Compressed file. Unzip it with a tool such as 7-Zip."),
        # Links
        "LINK": _("Link to an external website. Opens in a new tab."),
    }
    return tips.get(key)


def _filter_package_resources(resources: list[dict[str, Any]], q: str) -> list[dict[str, Any]]:
    """Filter resources by a free-text query against name, description and format."""
    if not q:
        return list(resources)

    needle = q.lower()
    matched = []
    for resource in resources:
        name = (tk.h.get_translated(resource, "name") or resource.get("name") or "").lower()
        description = (
            tk.h.get_translated(resource, "description") or resource.get("description") or ""
        ).lower()
        fmt = (resource.get("format") or "").lower()
        if needle in name or needle in description or needle in fmt:
            matched.append(resource)
    return matched


def _package_activity_count(package_id: str, activity_type: str | None = None) -> int:
    """Return the number of public activities about a package."""
    try:
        from ckanext.activity.logic.action import _get_user_permission_labels
        from ckanext.activity.model.activity import (
            _filter_activitites_from_type,
            _filter_activitites_from_users,
            _filter_activities_by_permission_labels,
            _package_activity_query,
        )
    except ImportError:
        return 0

    context: dict[str, Any] = {"user": tk.current_user.name, "auth_user_obj": tk.current_user}
    query = _filter_activitites_from_users(_package_activity_query(package_id))
    if activity_type:
        query = _filter_activitites_from_type(query, include=True, types=[activity_type])
    query = _filter_activities_by_permission_labels(query, _get_user_permission_labels(context))
    return int(query.count())


def _attach_resource_download_counts(
    resources: list[dict[str, Any]], package_id: str | None
) -> list[dict[str, Any]]:
    """Stamp ``num_downloads`` on resources for the panel (one query per render).

    Loaded only here — not on every ``package_show`` — via tracking's
    package-scoped aggregate. Missing tracking / package id leaves counts at 0.
    """
    downloads: dict[str, int] = {}
    if package_id and p.plugin_loaded("iadb_iar_tracking"):
        try:
            from ckanext.iadb_iar_tracking.tracking import EventReader
        except ImportError:
            EventReader = None  # type: ignore[misc, assignment]
        if EventReader is not None:
            downloads = EventReader().get_downloads_for_package_resources(package_id)

    return [
        {**resource, "num_downloads": downloads.get(resource["id"], 0)}
        if resource.get("id")
        else resource
        for resource in resources
    ]


def _sorted_package_resources(resources: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
    """Return a new list of resources sorted by the chosen option.

    Option names match ``idb_theme_highlights_sort_options``:
    ``data`` (temporal coverage), ``downloads``, ``created``, ``modified``.
    """
    items = list(resources)

    def modified_key(resource: dict[str, Any]) -> str:
        return resource.get("last_modified") or resource.get("metadata_modified") or resource.get("created") or ""

    if sort == "data":
        items.sort(
            key=lambda resource: (
                _year(resource.get("temporal_end")) or "",
                _year(resource.get("temporal_start")) or "",
                modified_key(resource),
            ),
            reverse=True,
        )
    elif sort == "downloads":
        items.sort(
            key=lambda resource: (
                resource.get("num_downloads") or 0,
                modified_key(resource),
            ),
            reverse=True,
        )
    elif sort == "created":
        items.sort(key=lambda resource: resource.get("created") or "", reverse=True)
    else:
        # ``modified`` (default): recently added or updated resources.
        items.sort(key=modified_key, reverse=True)

    return items


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
        # a portal with a page of all themes links it by chaining the helper
        "url": tk.h.url_for(f"{dataset_type}.search"),
    }


def idb_theme_main_nav() -> list[dict[str, Any]]:
    """Get the items of the main menu.

    name   - the item ID, for plugins that add items next to it.
    label  - the item text.
    url    - the page URL.
    active - whether the current page belongs to the item.

    Portal plugins add their pages by chaining the helper.
    """
    dataset_type = tk.h.default_package_type()
    group_type = tk.h.default_group_type("group")
    org_type = tk.h.default_group_type("organization")
    endpoint = (tk.request.endpoint or "") if has_request_context() else ""

    return [
        {
            "name": "datasets",
            "label": tk.h.humanize_entity_type("package", dataset_type, "main nav") or _("Datasets"),
            "url": tk.h.url_for(f"{dataset_type}.search"),
            "active": endpoint.startswith((dataset_type, f"{dataset_type}_resource")),
        },
        {
            "name": "groups",
            "label": tk.h.humanize_entity_type("group", group_type, "main nav") or _("Groups"),
            "url": tk.h.url_for(f"{group_type}.index"),
            "active": endpoint.startswith(group_type),
        },
        {
            "name": "organizations",
            "label": tk.h.humanize_entity_type("organization", org_type, "main nav") or _("Organizations"),
            "url": tk.h.url_for(f"{org_type}.index"),
            "active": endpoint.startswith(org_type),
        },
        {
            "name": "about",
            "label": _("About"),
            "url": tk.h.url_for("home.about"),
            "active": endpoint == "home.about",
        },
    ]


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
        # a portal with a page of all countries links it by chaining the helper
        "url": tk.h.url_for(f"{dataset_type}.search"),
    }


def idb_theme_advanced_search_config() -> dict[str, Any]:
    """Get the field definitions of the advanced search form.

    The keys are the Solr fields searched by the composite search plugin. The
    options of the dropdowns are the facet values of the datasets the current
    user can see, so every option matches at least one dataset.
    """
    select_fields = [
        ADVANCED_SEARCH_ORGANIZATION_FIELD,
        ADVANCED_SEARCH_FORMAT_FIELD,
        ADVANCED_SEARCH_LICENSE_FIELD,
    ]
    result = tk.get_action("package_search")(
        {"user": tk.current_user.name},
        {
            "rows": 0,
            "facet.field": select_fields,
            "facet.limit": -1,
            "include_private": tk.config.get("ckan.search.default_include_private"),
        },
    )
    facets = result.get("search_facets", {})

    def options(field: str) -> list[dict[str, str]]:
        items = facets.get(field, {}).get("items", [])
        return [
            {"value": item["name"], "label": item["display_name"]}
            for item in sorted(items, key=lambda item: item["display_name"].lower())
        ]

    term_placeholder = _("Enter a search term")
    definitions = {
        "text": {
            "type": "text",
            "label": _("Any attribute"),
            "placeholder": term_placeholder,
            "default": True,
        },
        "title": {
            "type": "text",
            "label": _("Dataset title"),
            "placeholder": term_placeholder,
        },
        "notes": {
            "type": "text",
            "label": _("Description"),
            "placeholder": term_placeholder,
        },
        ADVANCED_SEARCH_ORGANIZATION_FIELD: {
            "type": "select",
            "label": _("Organizational Unit"),
            "placeholder": _("Select an organizational unit"),
            "options": options(ADVANCED_SEARCH_ORGANIZATION_FIELD),
        },
        ADVANCED_SEARCH_FORMAT_FIELD: {
            "type": "select",
            "label": _("Format"),
            "placeholder": _("Select a format"),
            "options": options(ADVANCED_SEARCH_FORMAT_FIELD),
        },
        ADVANCED_SEARCH_LICENSE_FIELD: {
            "type": "select",
            "label": _("Licenses"),
            "placeholder": _("Select a license"),
            "options": options(ADVANCED_SEARCH_LICENSE_FIELD),
        },
        ADVANCED_SEARCH_TAGS_FIELD: {
            "type": "text",
            "label": _("Tags"),
            "placeholder": term_placeholder,
        },
    }

    # the text of the attached documents, extracted by ckanext-resource-indexer
    attachments_field = tk.config.get(ADVANCED_SEARCH_ATTACHMENTS_FIELD_OPTION)
    if attachments_field and p.plugin_loaded("resource_indexer"):
        definitions[attachments_field] = {
            "type": "text",
            "label": _("Document attachments"),
            "placeholder": term_placeholder,
        }

    return {
        "definitions": definitions,
        "order": list(definitions),
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
