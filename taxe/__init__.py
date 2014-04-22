# -*- coding: utf-8 -*-

from functools import wraps
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule

class Taxe(object):

    def __init__(self):
        self.urls = {}
        self.views = Map()

    def build(self, urls):
        self.urls = urls
        for key in urls:
            rule = Rule(key, methods=('GET', ), endpoint=key)
            self.views.add(rule)

    def dispatch_request(self, request):
        adapter = self.views.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            response = self.urls[endpoint]()
            return Response(response)
        except HTTPException, e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    application = Taxe()
    run_simple('localhost', 4000, application)
