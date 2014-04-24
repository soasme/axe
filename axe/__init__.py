# -*- coding: utf-8 -*-
"""
    Axe
    ~~~

    A microframework based on Werkzeug.

    :copyright: (c) 2014 by Ju Lin.
    :license: MIT, see LICENSE for more details.
"""

__all__ = [
    'abort',
    'redirect',

    'Axe',
]

__version__ = '0.0.1'

from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from .app import Axe
