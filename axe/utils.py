# -*- coding: utf-8 -*-

from werkzeug.exceptions import abort as _abort, HTTPException

def abort(http_status_code, **kwargs):
    try:
        _abort(http_status_code)
    except HTTPException as e:
        if len(kwargs):
            e.data = kwargs
        raise e
