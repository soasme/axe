# -*- coding: utf-8 -*-

import inspect
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule

def get_ext(name, app, request=None):
    return app.exts[name](request)

def query(request):
    return request.args

class Axe(object):

    DEFAULT_EXTS = {
        'query': query
    }

    def __init__(self):
        self.urls = {}
        self.exts = self.__class__.DEFAULT_EXTS
        self.views = Map()

    def build(self, urls):
        self.urls = urls
        for key in urls:
            rule = Rule(key, methods=('GET', ), endpoint=key)
            self.views.add(rule)

    def get_view(self, endpoint):
        return self.urls[endpoint]

    def get_view_args(self, view, request):
        arg_spec = inspect.getargspec(view)
        return {
            name: get_ext(name, self, request)
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
