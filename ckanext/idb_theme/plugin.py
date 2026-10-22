from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from typing_extensions import override

import ckan.plugins.toolkit as tk
from ckan import plugins as p

from ckanext.theming.base import BaseTheme
from ckanext.theming.interfaces import ITheme

from . import search
from .themes.idb.theme import make_theme


@tk.blanket.helpers
@tk.blanket.blueprints
@tk.blanket.config_declarations
class IdbThemePlugin(ITheme, p.IPackageController, p.SingletonPlugin):
    @override
    def register_themes(self) -> Iterable[BaseTheme]:
        return [make_theme()]

    # IPackageController

    @override
    def before_dataset_search(self, search_params: dict[str, Any]) -> dict[str, Any]:
        return search.datasets_page_search_params(search_params)
