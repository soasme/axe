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

def route_cookies(cookies):
    return cookies.get('key')

def route_posts(post_id):
    return 'This is post %s' % post_id

from axe import Axe
app = Axe()
app.build({
    '/query': route_query,
    '/form': route_form,
    '/json': route_json,
    '/headers': route_headers,
    '/method': route_method,
    '/body': route_body,
    '/cookies': route_cookies,
    '/posts/<int:post_id>': route_posts,
})
