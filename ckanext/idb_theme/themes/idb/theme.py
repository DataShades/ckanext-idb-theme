from __future__ import annotations

import os

from ckanext.theming.lib import Theme

here = os.path.dirname(__file__)


def make_theme(name: str = "idb"):
    return Theme(name, here)
