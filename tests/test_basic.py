# -*- coding: utf-8 -*-

from .suites.hello import app

def test_get_index():
    assert app.client.get('/').data == b'Index'

def test_get_hello():
    assert app.client.get('/hello').data == b'Hello World: [Anon]'

def test_get_hello_with_query():
    assert app.client.get('/hello?name=ainesmile').data == b'Hello World: ainesmile'

def test_get_404():
    assert app.client.get('/404').status_code == 404
