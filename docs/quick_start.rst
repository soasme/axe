.. _quickstart:

Quickstart
==========

This page gives a good introduction to Axe. You should have Axe installed first.

A Minimal Application
---------------------

A minimal Axe application looks something like this.
You can save it as `hello_world.py`::

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

::

    $ python hello_world.py

Now go to your browser and visit `http://127.0.0.1:8384/ <http://127.0.0.1:8384/>`_,
and you should see `Hello world!` in your screen.

To stop the server, hit Ctrl-C.
