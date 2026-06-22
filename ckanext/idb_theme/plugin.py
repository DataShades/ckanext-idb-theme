from __future__ import annotations
from collections.abc import Iterable

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckanext.theming.interfaces import ITheme

from ckanext.theming.base import BaseTheme
from typing_extensions import override
from .themes.idb.theme import make_theme

class IdbThemePlugin(ITheme, plugins.SingletonPlugin):

    @override
    def register_themes(self) -> Iterable[BaseTheme]:
        return [
            make_theme()
        ]
