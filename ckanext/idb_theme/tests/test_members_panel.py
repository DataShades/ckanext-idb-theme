from __future__ import annotations

import pytest

from ckan.lib.helpers import url_for
from ckan.tests import factories

pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "theming idb_theme"),
    pytest.mark.ckan_config("ckan.ui.theme", "idb"),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]

SEARCH_PLACEHOLDER = "Search members or role"


def _members_html(app, org, user) -> str:
    app.set_session_user(user["name"])
    response = app.get(url_for("organization.read", id=org["name"]))
    assert response.status_code == 200
    return response.body


def test_manager_sees_the_member_actions(app):
    """The pencil of the members panel edits the role of a member."""
    manager = factories.User()
    org = factories.Organization(
        users=[{"name": manager["name"], "capacity": "admin"}]
    )

    html = _members_html(app, org, manager)

    assert SEARCH_PLACEHOLDER in html
    assert "Action</th>" in html
    assert (
        url_for(
            "organization.member_new",
            id=org["id"],
            user=manager["id"],
        )
        in html
    )


def test_member_without_permissions_sees_no_actions(app):
    """Members that cannot manage the unit get the table without actions."""
    member = factories.User()
    org = factories.Organization(
        users=[{"name": member["name"], "capacity": "member"}]
    )

    html = _members_html(app, org, member)

    assert SEARCH_PLACEHOLDER in html
    assert "Action</th>" not in html
