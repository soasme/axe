# -*- coding: utf-8 -*-

def route_query(query):
    return query['hello']

def route_form(form):
    return form['hello']

def route_json(json):
    if not json:
        return 'Expected None JSON'
    return json['hello']

def route_headers(headers):
    return headers['hello']

def route_method(method):
    return method

def route_body(body):
    return body

from axe import Axe
app = Axe()
app.build({
    '/query': route_query,
    '/form': route_form,
    '/json': route_json,
    '/headers': route_headers,
    '/method': route_method,
    '/body': route_body,
})
