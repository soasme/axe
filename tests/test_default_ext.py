# -*- coding: utf-8 -*-

from .suites.default_ext import app

def test_query():
    assert app.client.get('/query?hello=world').data == b'world'

def test_form():
    assert app.client.post('/form', data={'hello': 'world'}).data == b'world'

def test_json():
    assert app.client.post('/json', data='{"hello":"world"}',
            headers={'Content-Type': 'application/json'}).data == b'world'

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
