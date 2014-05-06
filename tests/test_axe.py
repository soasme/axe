# -*- coding: utf-8 -*-

import pytest
from axe import Axe, errors

@pytest.fixture
def axe():
    return Axe()

@pytest.fixture
def axer():
    return Axe()

def test_build_from_urls(axe):
    func = lambda: ''
    axe.build({'/': func})
    assert '/' in axe.urls
    assert axe.urls['/'] == func

def test_register_ext_success(axe):
    @axe.ext
    def test(request):
        pass
    assert axe.exts['test'] == test

def test_register_ext_duplicated(axe):
    with pytest.raises(errors.DuplicatedExtension):
        @axe.ext
        def query(request):
            pass

def test_unrecognized_ext(axe):
    with pytest.raises(errors.UnrecognizedExtension):
        axe.build({'/': lambda unrecognized_ext: ''})

def test_proxy(axe, axer):
    axer.build({'/': lambda: 'hello', '/hello': lambda: 'world'})
    axe.proxy({'/axer': axer})
    assert axe.client.get('/axer').data == b'hello'
    assert axe.client.get('/axer/hello').data == b'world'

def test_add_route_dispatcher(axe, axer):
    axer.build({'/': lambda: 'hello', '/hello': lambda: 'world'})
    axe.add_route_dispatcher('/axer', axer)
    assert axe.client.get('/axer').data == b'hello'
    assert axe.client.get('/axer/hello').data == b'world'

def test_add_static_folder_success(axe, tmpdir):
    p = tmpdir.mkdir("sub").join("hello.css")
    p.write("body { background: black; }")
    axe.add_static_folder('/media', tmpdir.strpath)
    assert axe.client.get('/media/sub/hello.css').data == p.read()
