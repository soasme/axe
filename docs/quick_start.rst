.. _quickstart:

Quickstart
==========

This page gives a good introduction to Axe. You should have Axe installed first.

A Minimal Application
---------------------

A minimal Axe application looks something like this::

    from axe import Axe
    app = Axe()

    def index():
        return 'Hello World!'

    urls = {
        '/': index,
    }
    app.build(urls)

    if __name__ == '__main__':
        app.run_simple(host='127.0.0.1', port=8384)

You can save it as `hello_world.py`::

    $ python hello_world.py

Now go to your browser and visit `http://127.0.0.1:8384/ <http://127.0.0.1:8384/>`_,
and you should see `Hello world!` in your screen.

To stop the server, hit Ctrl-C.

WARNING: `run_simple` is for local development. It's strongly recommend
not to use in production environment.

.. _debug-mode:

Debug Mode
----------

If you pass `use_debugger=True` parameter to run_simple,
You will have an excellent debug stacktrace when the page occur error::

    app.run_simple(use_debugger=True)

If you pass `use_reloader=True` parameter to run_simple,
the server will auto restart whenever a file modified::

    app.run_simple(use_reloader=True)

More information about run_simple, see
`Werkzeug Documentation of run_simple <http://werkzeug.pocoo.org/docs/serving/#werkzeug.serving.run_simple>`_

Routing
-------

Static Serve
------------

Template
--------

It's you choice to use which template engine: Mako, Plim, Haml, Jinja, etc.
There is no default template engine now.

Dependency Injection
--------------------

The route controller functions always have many dependencies: query, form, json,
headers or any other specific of you project. But it's hard to debug if you
attach too much values in one `request` object. Here is the solution of `Axe`:
DI(Dependency Injection). List all the dependencies as parameter in controller
function, and happy to use them. We call these dependencies as extension in `Axe`.
There are several default extensions like `query`, `json`, `form`, `headers`,
`request`, `method`.  But `Axe` enable you to write your own extensions.


Redirects and Errors
--------------------

Use `axe.redirect` to direct the page::

    from axe import redirect, ext

    @ext
    def require_login(session):
        if not session:
            return redirect('/login')

    def index(require_login):
        return template('index.html')

    def login():
        return template('login')

    app.build({
        '/': index,
        '/login': login,
    })

Use `axe.error` to define the error action::

    from axe import error

    @error(404)
    def not_found(exc):
        return template('not_found.html')

About Response
--------------

Sessions
--------

Logging
-------

Scale Application
-----------------

When your project becomes big, it's better to split it into several small projects.
`Axe` allow you to assemble several WSGI application together when needed::

    from MyVanillaApiV1 import v1
    from MyVanillaApiV2 import v2
    from MyVanillaWeb import web
    app = Axe()
    app.proxy({
        '/api/1': v1,
        '/api/2': v2,
        '/': web,
    })
