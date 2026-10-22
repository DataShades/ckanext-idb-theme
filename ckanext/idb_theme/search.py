from __future__ import annotations

from typing import Any

from flask import has_request_context

import ckan.plugins.toolkit as tk

from .helpers import DATASET_SORTS, DEFAULT_DATASET_SORT, idb_theme_datasets_per_page


def datasets_page_search_params(search_params: dict[str, Any]) -> dict[str, Any]:
    """Apply the page size and the default sort of the Datasets page to its search.

    Only the main query of the dataset search view is changed: it is the one
    that uses ``ckan.datasets_per_page`` rows. Other searches made while
    rendering the page keep their parameters.
    """
    if not has_request_context() or tk.request.endpoint != f"{tk.h.default_package_type()}.search":
        return search_params

    if search_params.get("rows") != tk.config.get("ckan.datasets_per_page"):
        return search_params

    per_page = idb_theme_datasets_per_page()
    search_params["rows"] = per_page
    search_params["start"] = (tk.h.get_page_number(tk.request.args) - 1) * per_page

    if not tk.request.args.get("sort"):
        search_params["sort"] = DATASET_SORTS[DEFAULT_DATASET_SORT]

    return search_params
