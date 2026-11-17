"""Tests for the dataset change-history HTMX panel helpers."""

from __future__ import annotations

import pytest

from ckanext.idb_theme import helpers

THEME_PLUGINS = "theming idb_theme activity"


@pytest.mark.ckan_config("ckan.plugins", THEME_PLUGINS)
@pytest.mark.usefixtures("with_plugins")
class TestPackageActivity:
    def test_default_limit(self, app):
        pkg = {"id": "pkg-1", "name": "demo-dataset"}
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_activity(pkg, limit=9, offset=0)

        assert panel["limit"] == 9
        assert panel["offset"] == 0
        assert panel["limit_options"] == helpers.ACTIVITY_LIMIT_OPTIONS

    def test_unknown_limit_falls_back(self, app):
        pkg = {"id": "pkg-1", "name": "demo-dataset"}
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_activity(pkg, limit=99, offset=0)

        assert panel["limit"] == helpers.DEFAULT_ACTIVITY_LIMIT

    def test_unknown_activity_type_cleared(self, app):
        pkg = {"id": "pkg-1", "name": "demo-dataset"}
        with app.flask_app.test_request_context():
            panel = helpers.idb_theme_package_activity(
                pkg, activity_type="not-a-type", limit=9, offset=0
            )

        assert panel["activity_type"] == ""

    def test_activity_type_options_non_empty(self):
        options = helpers.idb_theme_activity_type_options()
        assert options
        assert any(option["value"] == "changed package" for option in options)

    def test_user_initials_from_fullname(self, monkeypatch):
        class FakeUser:
            fullname = "Veneri Guarch, Federico Alejandro"
            name = "fedeveneri"

        monkeypatch.setattr(helpers.model.User, "get", lambda ref: FakeUser())
        assert helpers.idb_theme_user_initials("user-1") == "VA"

    def test_user_initials_from_name_when_no_fullname(self, monkeypatch):
        class FakeUser:
            fullname = ""
            name = "fedeveneri"

        monkeypatch.setattr(helpers.model.User, "get", lambda ref: FakeUser())
        assert helpers.idb_theme_user_initials("user-1") == "FE"

    def test_activity_item_html_wraps_body_beside_avatar(self):
        item = (
            '<li class="item changed-package">'
            '<span class="fa-stack fa-lg">'
            '<i class="fa fa-circle fa-stack-2x icon"></i>'
            '<i class="fa fa-sitemap fa-stack-1x fa-inverse"></i>'
            "</span>"
            '<span>Actor</span> updated the dataset <span class="dataset">Demo</span>'
            "<br />"
            '<span class="date">2 days ago</span>'
            "</li>"
        )

        html = str(helpers.idb_theme_activity_item_html(item, "VA"))

        assert '<span class="change-history-avatar" aria-hidden="true">VA</span>' in html
        assert '<span class="change-history-body">' in html
        assert 'class="fa-stack' not in html
        assert html.index("change-history-avatar") < html.index("change-history-body")
        assert "Actor" in html
        assert 'class="date"' in html
        assert html.strip().endswith("</li>")
