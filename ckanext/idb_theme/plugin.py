from __future__ import annotations

from collections.abc import Iterable

from typing_extensions import override

import ckan.plugins.toolkit as tk
from ckan import plugins as p

from ckanext.theming.base import BaseTheme
from ckanext.theming.interfaces import ITheme

from .themes.idb.theme import make_theme


@tk.blanket.helpers
@tk.blanket.config_declarations
class IdbThemePlugin(ITheme, p.SingletonPlugin):
    @override
    def register_themes(self) -> Iterable[BaseTheme]:
        return [make_theme()]
