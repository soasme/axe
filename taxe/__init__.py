# -*- coding: utf-8 -*-

from functools import wraps
from werkzeug.wrappers import Request, Response

class Application(object):

    def route(self, url):
        def deco(function):
            @wraps(function)
            def _(*args, **kwargs):
                print self, url
                return function(*args, **kwargs)
            return _
        return deco

    @Request.application
    def __call__(self, request):
        return Response('Hello World')

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    application = Application()
    run_simple('localhost', 4000, application)
