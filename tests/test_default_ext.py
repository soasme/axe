# -*- coding: utf-8 -*-

from .suites.default_ext import app

# functional test

def test_query():
    assert app.client.get('/query?hello=world').data == b'world'

def test_form():
    assert app.client.post('/form', data={'hello': 'world'}).data == b'world'

def test_json():
    assert app.client.post('/json', data='{"hello":"world"}',
            headers={'Content-Type': 'application/json'}).data == b'world'

def test_broken_json():
    resp = app.client.post('/json', data='{"hello":"world}',
            headers={'Content-Type': 'application/json'})
    assert resp.status_code == 400

def test_content_type_is_not_application_json_then_request_body_is_not_json():
    assert app.client.post('/json', data='{"hello":"world"}',
            headers={'Content-Type': 'not/application/json'}
            ).data == b'Expected None JSON'

def test_headers():
    assert app.client.get('/headers', headers={'hello': 'world'}).data == b'world'

def test_method_get():
    assert app.client.get('/method').data == b'GET'

def test_method_post():
    assert app.client.post('/method').data == b'POST'

def test_method_put():
    assert app.client.put('/method').data == b'PUT'

def test_method_delete():
    assert app.client.delete('/method').data == b'DELETE'

# TODO: we need to support head/options/patch

def test_body():
    assert app.client.post('/body', data='Whatever').data == b'Whatever'

def test_cookies():
    assert app.client.get('/cookies', headers={'COOKIE': 'key=value;'}).data == b'value'

def test_args_in_route():
    assert app.client.get('/posts/1').data == b'This is post 1'
