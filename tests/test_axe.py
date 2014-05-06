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

def test_get_ext_by_name(axe):
    @axe.ext
    def test(request):
        pass
    assert axe.get_ext('test') == test

def test_get_view(axe):
    view = lambda: 'view'
    axe.build({'/view': view})
    assert axe.get_view('/view') == view

def test_if_view_does_not_exist(axe):
    pytest.raises(errors.MissingEndpoint, axe.get_view, '/view')

def test_get_request_ext_if_view_has_only_one_request(axe):
    view = lambda request: ''
    axe.build({'/': view})
    assert axe.get_view_args(view, 'request') == {'request': 'request'}

def test_get_request_ext_with_other(axe):
    @axe.ext
    def others(request):
        return 'others'
    view = lambda request, others: ''
    axe.build({'/': view})
    assert axe.get_view_args(view, 'request') == {
        'request': 'request',
        'others': 'others'
    }

def test_get_ext_without_request(axe):
    @axe.ext
    def whatever(request):
        return 'whatever'
    view = lambda whatever: ''
    axe.build({'/': view})
    assert axe.get_view_args(view, 'request') == {'whatever': 'whatever'}

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
    content = b"body { background: black; }"
    p.write(content)
    axe.add_static_folder('/media', tmpdir.strpath)
    assert axe.client.get('/media/sub/hello.css').data == content

