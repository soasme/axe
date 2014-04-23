# -*- coding: utf-8 -*-

def route_query(query):
    return query['hello']

def route_form(form):
    return form['hello']

def route_json(json):
    return json['hello']

def route_headers(headers):
    return headers['hello']

from axe import Axe
app = Axe()
app.build({
    '/query': route_query,
    '/form': route_form,
    '/json': route_json,
    '/headers': route_headers,
})
