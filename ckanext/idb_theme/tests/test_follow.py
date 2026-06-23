from __future__ import annotations

import pytest

from ckan.lib.helpers import url_for
from ckan.tests import factories

pytestmark = [
    pytest.mark.usefixtures("with_plugins", "clean_db"),
    pytest.mark.ckan_config("ckan.auth.public_user_details", False),
]


def test_non_admin_can_follow_and_unfollow_group(app):
    user = factories.User()
    group = factories.Group()
    app.set_session_user(user["name"])

    response = app.post(url_for("idb_theme.group_follow", id=group["id"]))

    assert response.status_code == 200
    assert "Unfollow" in response

    response = app.post(url_for("idb_theme.group_unfollow", id=group["id"]))

    assert response.status_code == 200
    assert "Follow" in response


def test_non_admin_can_follow_and_unfollow_organization(app):
    user = factories.User()
    organization = factories.Organization()
    app.set_session_user(user["name"])

    response = app.post(url_for("idb_theme.organization_follow", id=organization["id"]))

    assert response.status_code == 200
    assert "Unfollow" in response

    response = app.post(url_for("idb_theme.organization_unfollow", id=organization["id"]))

    assert response.status_code == 200
    assert "Follow" in response
