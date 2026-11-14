"""Tests for the dataset resources HTMX panel helpers."""

from __future__ import annotations

import pytest

from ckanext.idb_theme import helpers

THEME_PLUGINS = "theming idb_theme"


def _pkg(*names: str, **resource_overrides) -> dict:
    resources = []
    for index, name in enumerate(names):
        resource = {
            "id": f"res-{name}",
            "name": name,
            "description": f"Description of {name}",
            "position": index,
            "created": f"2024-01-{index + 1:02d}T00:00:00",
            "last_modified": f"2024-02-{index + 1:02d}T00:00:00",
            "temporal_start": f"200{index}-01-01",
            "temporal_end": f"201{index}-12-31",
            "num_downloads": index,
        }
        overrides = resource_overrides.get(name) or {}
        resource.update(overrides)
        resources.append(resource)
    return {"name": "demo-dataset", "resources": resources}


@pytest.mark.ckan_config("ckan.plugins", THEME_PLUGINS)
@pytest.mark.usefixtures("with_plugins")
class TestPackageResources:
    def test_default_limit_and_sort(self, app):
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_resources(
                _pkg("a", "b", "c", "d", "e"), sort="modified", limit=4, offset=0
            )

        assert panel["limit"] == 4
        assert panel["sort"] == "modified"
        assert panel["item_count"] == 5
        # Most recently updated first (e has the latest last_modified).
        assert [resource["name"] for resource in panel["resources"]] == ["e", "d", "c", "b"]
        assert panel["first_item"] == 1
        assert panel["last_item"] == 4
        assert panel["next_url"]
        assert panel["previous_url"] is None

    def test_offset_pagination(self, app):
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_resources(
                _pkg("a", "b", "c", "d", "e"), sort="modified", limit=4, offset=4
            )

        assert [resource["name"] for resource in panel["resources"]] == ["a"]
        assert panel["first_item"] == 5
        assert panel["last_item"] == 5
        assert panel["previous_url"]
        assert panel["next_url"] is None

    def test_sort_by_created(self, app):
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_resources(
                _pkg("beta", "alpha", "gamma"), sort="created", limit=8, offset=0
            )

        assert [resource["name"] for resource in panel["resources"]] == ["gamma", "alpha", "beta"]

    def test_sort_by_temporal_data(self, app):
        pkg = _pkg(
            "old",
            "new",
            "mid",
            old={"temporal_end": "2010-12-31", "temporal_start": "2000-01-01"},
            new={"temporal_end": "2024-12-31", "temporal_start": "2020-01-01"},
            mid={"temporal_end": "2018-12-31", "temporal_start": "2015-01-01"},
        )
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_resources(pkg, sort="data", limit=8, offset=0)

        assert [resource["name"] for resource in panel["resources"]] == ["new", "mid", "old"]

    def test_sort_by_downloads(self, app, monkeypatch):
        pkg = _pkg("low", "high", "mid")
        pkg["id"] = "pkg-1"
        monkeypatch.setattr(
            helpers,
            "_attach_resource_download_counts",
            lambda resources, package_id: [
                {
                    **resource,
                    "num_downloads": {"res-low": 1, "res-high": 50, "res-mid": 10}[resource["id"]],
                }
                for resource in resources
            ],
        )
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_resources(pkg, sort="downloads", limit=8, offset=0)

        assert [resource["name"] for resource in panel["resources"]] == ["high", "mid", "low"]
        assert [resource["num_downloads"] for resource in panel["resources"]] == [50, 10, 1]

    def test_unknown_sort_and_limit_fall_back(self, app):
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_resources(_pkg("a", "b"), sort="nope", limit=99, offset=0)

        assert panel["sort"] == helpers.DEFAULT_RESOURCE_SORT
        assert panel["limit"] == helpers.DEFAULT_RESOURCE_LIMIT

    def test_search_filters_by_name(self, app):
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_resources(
                _pkg("alpha-data", "beta-report", "gamma-data"),
                sort="modified",
                limit=8,
                offset=0,
                q="data",
            )

        assert [resource["name"] for resource in panel["resources"]] == ["gamma-data", "alpha-data"]
        assert panel["q"] == "data"
        assert panel["item_count"] == 2

    def test_resource_sort_options_match_highlights(self):
        assert helpers.idb_theme_resource_sort_options() == helpers.idb_theme_highlights_sort_options()

    def test_resource_card_includes_format_and_size(self, app):
        pkg = {
            "type": "dataset",
            "name": "demo-dataset",
        }
        resource = {
            "id": "res-1",
            "name": "Table",
            "description": "A CSV table",
            "format": "CSV",
            "byteSize": "228065280",
            "temporal_start": "2001-01-01",
            "temporal_end": "2014-12-31",
            "url_type": "upload",
            "url": "http://example.com/table.csv",
            "num_downloads": 1814,
        }

        with app.flask_app.test_request_context():
            card = helpers.idb_theme_resource_card(pkg, resource)

        assert card["format"] == "CSV"
        assert card["coverage"] == ["2001", "2014"]
        assert card["downloads"] == 1814
        assert card["size"]
        assert card["format_tip"]
        assert card["download_url"]
        assert card["preview_url"]
