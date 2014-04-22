# -*- coding: utf-8 -*-

import pytest

from .suites.hello import app
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

@pytest.fixture
def client():
    return Client(app, BaseResponse)

def test_get_index(client):
    assert client.get('/').data == 'Index'

def test_get_hello(client):
    assert client.get('/hello').data == 'Hello World: [Anon]'

def test_get_hello_with_query(client):
    assert client.get('/hello?name=ainesmile').data == 'Hello World: ainesmile'

def test_get_404(client):
    assert client.get('/404').status_code == 404
