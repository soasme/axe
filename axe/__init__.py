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

    @Request.application
    def __call__(self, request):
        adapter = self.views.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            view = self.urls[endpoint]
            arg_spec = inspect.getargspec(view)
            values = {
                name: get_ext(name, self, request)
                for name in arg_spec.args
            }
            resp = view(**values)
            return Response(resp)
        except HTTPException, e:
            return e



if __name__ == '__main__':
    from werkzeug.serving import run_simple
    application = Taxe()
    run_simple('localhost', 4000, application)
