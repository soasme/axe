# -*- coding: utf-8 -*-

import inspect

from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import DispatcherMiddleware

from .errors import (
    DuplicatedExtension,
    UnrecognizedExtension,
    MissingEndpoint,
)
from .default_exts import (
    get_query,
    get_form,
    get_json,
    get_headers,
    get_method,
    get_body,
    get_cookies,
    get_request,
)

class Axe(object):

    DEFAULT_EXTS = {
        'query': get_query,
        'form': get_form,
        'json': get_json,
        'headers': get_headers,
        'method': get_method,
        'body': get_body,
        'cookies': get_cookies,
        'request': get_request,
    }

    def __init__(self):
        self.urls = {}
        self.proxies = {}
        self.exts = dict(self.__class__.DEFAULT_EXTS)
        self.views = Map()
        self._wsgi_app = self.axe_wsgi_app

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

    def ext(self, func):
        func_name = func.__name__
        if func_name in self.exts:
            raise DuplicatedExtension
        self.exts[func_name] = func
        return func

    def get_view(self, endpoint):
        try:
            return self.urls[endpoint]
        except KeyError:
            raise MissingEndpoint

    def get_view_args(self, view, request, cache):
        arg_spec = inspect.getargspec(view)
        if 'request' in arg_spec.args:
            cache.update({'request': request})

        args = {}
        for name in arg_spec.args:
            if name in cache:
                args[name] = cache[name]
            else:
                func = self.get_ext(name)
                func_args = self.get_view_args(func, request, cache)
                args[name] = func(**func_args)
                cache[name] = args[name]

        return args

    def gen_response(self, request):
        adapter = self.views.bind_to_environ(request.environ)
        endpoint, values = adapter.match()
        view = self.get_view(endpoint)
        args = self.get_view_args(view, request, cache={})
        resp = view(**args)
        return Response(resp)

    def wsgi_app(self, env, start_response):
        return self._wsgi_app(env, start_response)

    __call__ = wsgi_app

    @Request.application
    def axe_wsgi_app(self, request):
        try:
            return self.gen_response(request)
        except HTTPException as e:
            return e

    @property
    def client(self):
        from werkzeug.test import Client
        return Client(self, Response)

    def run_simple(self, host='127.0.0.1', port='8384', **options):
        from werkzeug.serving import run_simple
        run_simple(host, port, self, **options)

    def add_static_folder(self, route, path):
        from werkzeug.wsgi import SharedDataMiddleware
        self._wsgi_app = SharedDataMiddleware(
            self._wsgi_app, {
                route: path
            }
        )

    def add_route_dispatcher(self, route, wsgi_app):
        self._wsgi_app = DispatcherMiddleware(
            self._wsgi_app, {
                route: wsgi_app
            }
        )

    def proxy(self, mounts):
        self.mounts = mounts
        self._wsgi_app = DispatcherMiddleware(
            self._wsgi_app,
            mounts
        )
