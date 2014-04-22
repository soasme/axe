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
    return client.get('/hello').data == 'Hello World: '
