# -*- coding: utf-8 -*-

import json
from werkzeug.exceptions import BadRequest

def get_request(request):
    return request

def get_query(request):
    return request.args

def get_form(request):
    return request.form

def get_body(request):
    return request.data

def get_headers(request):
    return request.headers

def get_method(request):
    return request.method

def get_json(headers, body):
    content_type = headers.get('Content-Type')
    if content_type != 'application/json':
        return
    data = body.decode('utf8')
    try:
        return json.loads(data)
    except ValueError:
        raise BadRequest('Broken JSON data')
