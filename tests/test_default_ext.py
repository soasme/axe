# -*- coding: utf-8 -*-

import pytest

from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from .suites.default_ext import app

@pytest.fixture
def client():
    return Client(app, BaseResponse)

def test_query(client):
    assert client.get('/query?hello=world').data == b'world'

def test_form(client):
    assert client.post('/form', data={'hello': 'world'}).data == b'world'

def test_json(client):
    assert client.post('/json', data='{"hello":"world"}',
            headers={'Content-Type': 'application/json'}).data == b'world'

def test_headers(client):
    assert client.get('/headers', headers={'hello': 'world'}).data == b'world'
