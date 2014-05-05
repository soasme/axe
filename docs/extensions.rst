.. _extensions:

Extensions
==========

The purpose of Axe extensions is to provide a readable
baseline which makes view function can reliably and
transparently execute. Axe extension mechanism offer
dramatic improvements over attaching values with
global context.

* Extensions have explicit names and are activated only
  when need it.
* Each extension name triggers an extension function
  which can itself use other extensions.

Extensions as View Function arguments
-------------------------------------

View functions can receive extension objects by naming
them as an input argument. For each argument name, an
extension function with that name provides the
extension object. After initialize Axe app, `app = Axe()`,
Extension functions as registered by decorating them
with `@app.ext`. Let's look at a simple self-contained
Axe app containing a customized extension::

    from axe import Axe
    import os
    app = Axe()

    @app.ext
    def config():
        return {'system': os.name}

    def index(config):
        return config.get('system', 'Unknown')

    app.build({'/': index})

    if __name__ == '__main__':
        app.run_simple()

Here, the `index` view function needs the `config`
extension value. Axe app will discover all the
extensions that registered to it and call the
`@app.ext` marked `config` extension function.
Running this example, and visit '/'::

    ~ % curl http://localhost:8384
    posix

You might got a different result, but that's trivial.
Here is the exact process executed by Axe to call
view function this way:

1. curl make a request of '/', and Axe app route '/' to
   `index` view function.
2. `index` view function needs a function argument
   named `config`. A matching extension is discovered
   by looking for an extension-decorated function
   named `config`.
3. `config()` is called and return a dict result.
4. `index({'system': 'posix'})` is actully called
   and the rest is view function logic: get key
   `system` in `config` dict as response body.

Note that if you misspell a function argument or want
to use one that isn't available, you will see an error
`axe.errors.UnrecognizedExtension` before app running,
alas, the app is failed to start.

Sharing an extension across view functions
------------------------------------------

The extension can be applied into all view functions
that is built by `app.build`. Multiple view functions
after building will each receive the same extension
function, and build it within every request.

Chain
-----

You can not only use extensions in view functions but
extension functions can use other extensions themselves.
Here is a default extension `json` offered by Axe::

    @app.ext
    def json(headers, body):
        content_type = headers.get('Content-Type')
        if content_type != 'application/json':
            return
        data = body.decode('utf8')
        try:
            return json.loads(data)
        except ValueError:
            raise BadJSON

Note that avoid writing circular dependency for
extensions.


Modularity
----------

You might got mad by writing many input parameters in a
view function. As we have ability to chaining extensions,
Here is a simple example for you to extend the previous
`config` example. We instantiate an object `exts` where 
we stick the already defined `config` resource into it::

    class Exts(object):
        def __init__(config):
            self.config = config

    @app.ext
    def exts(config):
        return Exts(config)

    def index(exts):
        return exts.config.get('system')
