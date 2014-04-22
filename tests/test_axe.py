# -*- coding: utf-8 -*-

import pytest
from axe import Axe, errors

@pytest.fixture
def axe():
    return Axe()

def test_build_from_urls(axe):
    func = lambda: ''
    axe.build({'/': func})
    assert '/' in axe.urls
    assert axe.urls['/'] == func

def test_register_ext_success(axe):
    @axe.register_ext
    def test(request):
        pass
    assert axe.exts['test'] == test

def test_register_ext_duplicated(axe):
    with pytest.raises(errors.DuplicatedExtension):
        @axe.register_ext
        def query(request):
            pass
