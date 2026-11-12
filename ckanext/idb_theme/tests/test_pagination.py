from __future__ import annotations

from typing import Any

import pytest

import ckan.plugins.toolkit as tk
from ckan.tests import factories

from ckanext.idb_theme import search

THEME_PLUGINS = "theming idb_theme"
PER_PAGE = 3


class TestDatasetsPageSearchParams:
    """The page size of the "Items per page" dropdown applies to the search."""

    def test_dataset_search_gets_the_page_size(self, app):
        params = _params(app, "/dataset?_per_page=8", rows=tk.config["ckan.datasets_per_page"], start=0)

        assert params["rows"] == 8
        assert params["start"] == 0

    def test_dataset_search_gets_the_default_sort(self, app):
        params = _params(app, "/dataset", rows=tk.config["ckan.datasets_per_page"])

        assert params["sort"] == search.DATASET_SORTS[search.DEFAULT_DATASET_SORT]

    def test_dataset_search_keeps_the_selected_sort(self, app):
        params = _params(app, "/dataset?sort=title asc", rows=tk.config["ckan.datasets_per_page"])

        assert "sort" not in params

    def test_organization_page_gets_the_page_size(self, app):
        params = _params(app, "/organization/some-org?page=2&_per_page=8", rows=tk.config["ckan.datasets_per_page"])

        assert params["rows"] == 8
        assert params["start"] == 8

    def test_organization_page_keeps_the_relevance_sort(self, app):
        params = _params(app, "/organization/some-org", rows=tk.config["ckan.datasets_per_page"])

        assert "sort" not in params

    def test_group_page_gets_the_page_size(self, app):
        params = _params(app, "/group/some-group?_per_page=16", rows=tk.config["ckan.datasets_per_page"])

        assert params["rows"] == 16
        assert params["start"] == 0

    def test_other_searches_are_untouched(self, app):
        # e.g. the counts of the datasets shown on the page
        rows = tk.config["ckan.datasets_per_page"]
        params = _params(app, "/organization/some-org?_per_page=8", rows=rows - 1)

        assert params["rows"] == rows - 1

    def test_searches_of_other_pages_are_untouched(self, app):
        params = _params(app, "/about?_per_page=8", rows=tk.config["ckan.datasets_per_page"])

        assert params["rows"] == tk.config["ckan.datasets_per_page"]


@pytest.mark.ckan_config("ckan.plugins", THEME_PLUGINS)
@pytest.mark.ckan_config("ckan.ui.theme", "idb")
@pytest.mark.ckan_config("ckan.datasets_per_page", PER_PAGE)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestOrganizationPagePagination:
    """The organization page paginates its datasets as the Datasets page does."""

    def test_page_shows_its_own_datasets(self, app):
        org, names = _organization_with_datasets(5)
        first = app.get(f"/organization/{org['name']}").get_data(as_text=True)

        page = app.get(f"/organization/{org['name']}?page=2").get_data(as_text=True)

        # the search sorts the datasets, so the pages are compared by their
        # content instead of the creation order
        first_names = _datasets_on(first, names)

        assert len(first_names) == PER_PAGE
        # the datasets of the first page are not repeated
        assert set(_datasets_on(page, names)) == set(names) - set(first_names)
        assert "No datasets match your search" not in page

    def test_page_size_of_the_dropdown_is_honoured(self, app):
        org, names = _organization_with_datasets(5)

        page = app.get(f"/organization/{org['name']}?_per_page=8").get_data(as_text=True)

        for name in names:
            assert name in page

    def test_htmx_request_swaps_the_results_only(self, app):
        org, names = _organization_with_datasets(5)
        first = app.get(f"/organization/{org['name']}").get_data(as_text=True)

        page = app.get(f"/organization/{org['name']}?page=2", headers={"HX-Request": "true"}).get_data(
            as_text=True
        )

        assert 'id="search-results"' in page
        assert 'id="search-facets"' in page
        first_names = _datasets_on(first, names)
        assert set(_datasets_on(page, names)) == set(names) - set(first_names)
        # the dataset page only parts must not be rendered on this page
        assert "dataset-search-hero-filters" not in page
        assert "dataset-search-results-header" not in page


@pytest.mark.ckan_config("ckan.plugins", THEME_PLUGINS)
@pytest.mark.ckan_config("ckan.ui.theme", "idb")
@pytest.mark.ckan_config("ckan.datasets_per_page", PER_PAGE)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_datasets_page_shows_the_results_of_its_pages(app):
    """The results of the page after the first one are rendered (see `page` checks)."""
    org, names = _organization_with_datasets(5)
    first = app.get(f"/dataset?organization={org['name']}").get_data(as_text=True)

    page = app.get(f"/dataset?organization={org['name']}&page=2&_per_page={PER_PAGE}").get_data(as_text=True)

    first_names = _datasets_on(first, names)

    assert len(first_names) == PER_PAGE
    assert set(_datasets_on(page, names)) == set(names) - set(first_names)
    assert "No datasets match your search" not in page


def _params(app: Any, url: str, **params: Any) -> dict[str, Any]:
    with app.flask_app.test_request_context(url):
        return search.datasets_page_search_params(dict(params))


def _organization_with_datasets(count: int) -> tuple[dict[str, Any], list[str]]:
    org = factories.Organization()
    names = []

    for _ in range(count):
        dataset = factories.Dataset(owner_org=org["id"])
        names.append(dataset["name"])

    return org, names


def _datasets_on(html: str, names: list[str]) -> list[str]:
    """Return the datasets of the page, in their creation order."""
    return [name for name in names if name in html]
