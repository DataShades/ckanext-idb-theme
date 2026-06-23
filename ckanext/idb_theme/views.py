from __future__ import annotations

from flask import Blueprint

import ckan.plugins.toolkit as tk
from ckan.common import current_user

__all__ = ["bp"]

bp = Blueprint("idb_theme", __name__, url_prefix="/idb-theme")


# Temporary hotfix for https://github.com/ckan/ckan/pull/9394.
def _follow_group(id: str, *, is_organization: bool, follow: bool) -> str:
    group_type = "organization" if is_organization else "group"
    data_dict = {
        "id": id,
        "include_datasets": True,
        "include_users": False,
    }
    if not follow:
        data_dict["include_followers"] = True

    extra_vars = {
        "current_user": current_user,
        "show_nums": True,
    }

    try:
        action = "organization_show" if is_organization else "group_show"
        group_dict = tk.get_action(action)({}, data_dict)
    except (tk.ObjectNotFound, tk.NotAuthorized):
        msg = tk._(f"{group_type} not found or you have no permission to view it")
        tk.abort(404, msg)

    error_message = ""
    try:
        if follow:
            tk.get_action("follow_group")({}, {"id": id})
            extra_vars["am_following"] = True
        else:
            tk.get_action("unfollow_group")({}, {"id": id})
            extra_vars["am_following"] = False
    except tk.ValidationError as error:
        error_message = error.error_summary

    extra_vars["error_message"] = error_message

    if is_organization:
        extra_vars["organization"] = group_dict
        return tk.render("organization/snippets/info.html", extra_vars)

    extra_vars["group"] = group_dict
    return tk.render("group/snippets/info.html", extra_vars)


@bp.post("/group/follow/<id>")
def group_follow(id: str) -> str:
    return _follow_group(id, is_organization=False, follow=True)


@bp.post("/group/unfollow/<id>")
def group_unfollow(id: str) -> str:
    return _follow_group(id, is_organization=False, follow=False)


@bp.post("/organization/follow/<id>")
def organization_follow(id: str) -> str:
    return _follow_group(id, is_organization=True, follow=True)


@bp.post("/organization/unfollow/<id>")
def organization_unfollow(id: str) -> str:
    return _follow_group(id, is_organization=True, follow=False)
