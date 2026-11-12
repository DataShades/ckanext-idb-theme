from __future__ import annotations

import re

import pytest

from ckan.tests import factories

THEME_PLUGINS = "theming idb_theme"
COUNT = r"(\d+|No) datasets? found"
SUMMARY = r'<div id="dataset-search-summary"([^>]*)>'

pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", THEME_PLUGINS),
    pytest.mark.ckan_config("ckan.ui.theme", "idb"),
    pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index"),
]


def test_organization_page_shows_the_number_of_found_datasets(app):
    organization = factories.Organization()
    factories.Dataset(owner_org=organization["id"])
    factories.Dataset(owner_org=organization["id"])

    page = app.get(f"/organization/{organization['name']}").get_data(as_text=True)

    assert _count(page) == "2 datasets found"
    assert 'hx-swap="none"' in _summary_attrs(page)
    assert "hx-swap-oob" not in _summary_attrs(page)


def test_organization_page_updates_the_count_on_htmx_requests(app):
    """The count is outside the swapped results, so it is swapped as well."""
    organization = factories.Organization()
    factories.Dataset(owner_org=organization["id"], resources=[{"format": "PDF"}])
    factories.Dataset(owner_org=organization["id"])

    page = app.get(
        f"/organization/{organization['name']}?res_format=PDF",
        headers={"HX-Request": "true"},
    ).get_data(as_text=True)

    assert _count(page) == "1 dataset found"
    assert "hx-swap-oob" in _summary_attrs(page)
    # the applied filters and the filters button follow the facets as well
    assert "Remove applied filter: PDF" in page


def test_organization_page_renders_the_filters_button(app):
    """The button opens the filters panel on mobile, it must be on the page."""
    organization = factories.Organization()
    factories.Dataset(owner_org=organization["id"], resources=[{"format": "PDF"}])

    page = app.get(f"/organization/{organization['name']}").get_data(as_text=True)

    assert 'class="show-filters btn"' in page

    fragment = app.get(
        f"/organization/{organization['name']}?res_format=PDF",
        headers={"HX-Request": "true"},
    ).get_data(as_text=True)

    assert 'class="show-filters btn"' in fragment
    assert "show-filters-count" in fragment


def test_group_page_updates_the_count_and_keeps_the_search_form(app):
    """The results of a group page contain the search form with the count."""
    group = factories.Group()
    factories.Dataset(groups=[{"name": group["name"]}], tags=[{"name": "Social"}])
    factories.Dataset(groups=[{"name": group["name"]}])

    page = app.get(
        f"/group/{group['name']}?tags=Social", headers={"HX-Request": "true"}
    ).get_data(as_text=True)

    assert _count(page) == "1 dataset found"
    assert 'id="dataset-search-form"' in page


def test_datasets_page_keeps_its_own_results_header(app):
    factories.Dataset(tags=[{"name": "Social"}])
    factories.Dataset()

    page = app.get("/dataset?tags=Social", headers={"HX-Request": "true"}).get_data(
        as_text=True
    )

    assert _count(page) == "1 dataset found"
    assert 'id="dataset-search-results-header"' in page
    assert "dataset-search-summary" not in page


def test_organization_page_search_form_does_not_swap_the_page(app):
    """The response to the form is a fragment.

    Swapping it into the page body would leave the page without its layout.
    """
    organization = factories.Organization()
    factories.Dataset(owner_org=organization["id"])

    page = app.get(f"/organization/{organization['name']}").get_data(as_text=True)

    assert 'hx-swap="none"' in _form_attrs(page, "dataset-search-form")
    assert "<html" not in app.get(
        f"/organization/{organization['name']}?q=data", headers={"HX-Request": "true"}
    ).get_data(as_text=True).lower()


def test_index_page_search_form_swaps_the_page(app):
    """The index pages answer htmx requests with the whole page."""
    factories.Organization()

    page = app.get("/organization").get_data(as_text=True)

    assert "hx-swap" not in _form_attrs(page, "organization-search-form")


def _count(page: str) -> str | None:
    match = re.search(COUNT, page)

    return match.group(0) if match else None


def _summary_attrs(page: str) -> str:
    match = re.search(SUMMARY, page)

    return match.group(1) if match else "<missing>"


def _form_attrs(page: str, form_id: str) -> str:
    match = re.search(rf'<form\b[^>]*id="{form_id}"[^>]*>', page, re.S)

    return match.group(0) if match else "<missing>"
