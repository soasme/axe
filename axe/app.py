# -*- coding: utf-8 -*-

import inspect

from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response

from .errors import (
    DuplicatedExtension,
    UnrecognizedExtension,
)
from .default_exts import (
    get_query,
    get_form,
    get_json,
    get_headers,
    get_method,
    get_request,
)

class Axe(object):

    DEFAULT_EXTS = {
        'query': get_query,
        'form': get_form,
        'json': get_json,
        'headers': get_headers,
        'method': get_method,
        'request': get_request,
    }

    def __init__(self):
        self.urls = {}
        self.exts = dict(self.__class__.DEFAULT_EXTS)
        self.views = Map()
        self._wsgi_app = self.wsgi_app

    def build(self, urls):
        self.urls = urls
        for key in urls:
            rule = Rule(key, endpoint=key)
            arg_spec = inspect.getargspec(urls[key])
            for ext in arg_spec.args:
                self.get_ext(ext)
            self.views.add(rule)

    def get_ext(self, name):
        try:
            return self.exts[name]
        except KeyError:
            raise UnrecognizedExtension(name)

    def get_ext_value(self, name, request=None):
        return self.get_ext(name)(request)

    def ext(self, func):
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
            name: self.get_ext_value(name, request)
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
    def wsgi_app(self, request):
        try:
            return self.gen_response(request)
        except HTTPException as e:
            return e

    def __call__(self, env, start_response):
        app = self._wsgi_app
        return app(env, start_response)

    @property
    def client(self):
        from werkzeug.test import Client
        return Client(self, Response)

    def run_simple(self, host='127.0.0.1', port='8384', **options):
        from werkzeug.serving import run_simple
        run_simple(host, port, self, **options)

    def add_static_folder(self, route, path):
        from werkzeug.wsgi import SharedDataMiddleware
        self._wsgi_app = SharedDataMiddleware(self._wsgi_app, {
            route: path
        })

    def add_route_dispatcher(self, route, wsgi_app):
        from werkzeug.wsgi import DispatcherMiddleware
        self._wsgi_app = DispatcherMiddleware(self._wsgi_app, {
            route: wsgi_app
        })
