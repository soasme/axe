# -*- coding: utf-8 -*-

import inspect
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule

from .errors import (
    DuplicatedExtension,
)
from .default_exts import (
    query,
)


class Axe(object):

    DEFAULT_EXTS = {
        'query': query
    }

    def __init__(self):
        self.urls = {}
        self.exts = dict(self.__class__.DEFAULT_EXTS)
        self.views = Map()

    def build(self, urls):
        self.urls = urls
        for key in urls:
            rule = Rule(key, endpoint=key)
            self.views.add(rule)

    def get_ext(self, name, request=None):
        return self.exts[name](request)

    def register_ext(self, func):
        func_name = func.__name__
        if func_name in self.exts:
            raise DuplicatedExtension
        self.exts[func_name] = func
        return func

    def get_view(self, endpoint):
        return self.urls[endpoint]

    def get_view_args(self, view, request):
        arg_spec = inspect.getargspec(view)
        return {
            name: self.get_ext(name, request)
            for name in arg_spec.args
        }

    def gen_response(self, request):
        adapter = self.views.bind_to_environ(request.environ)
        endpoint, values = adapter.match()
        view = self.get_view(endpoint)
        args = self.get_view_args(view, request)
        resp = view(**args)
        return Response(resp)

    @Request.application
    def __call__(self, request):
        try:
            return self.gen_response(request)
        except HTTPException as e:
            return e
