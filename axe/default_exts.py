# -*- coding: utf-8 -*-

import json

def get_request(request):
    return request

def get_query(request):
    return request.args

def get_form(request):
    return request.form

def get_json(request):
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return
    data = request.data.decode('utf8')
    return json.loads(data)

def get_headers(request):
    return request.headers

def get_method(request):
    return request.method
