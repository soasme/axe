# -*- coding: utf-8 -*-

from werkzeug.exceptions import BadRequest

class BadJSON(BadRequest):
    description = 'Bad JSON data'
