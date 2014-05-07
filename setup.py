# -*- coding: utf-8 -*-
"""
- What is Axe?

Axe is an extremely extendable web framework for Python based on `Werkzeug`.
It help developer keep project easy to extend and test when project grows.

Unlike Flask, there is no **Thread-Local** variables like `flask.request`, `flask.g`.
All variable are injected into view function through function name inspired by `py.test fixture`.

**Warning**: It's still experimental and has many buggy.

- Example

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


- Where can I get help?

You can ask any question in [Github Issue](https://github.com/soasme/axe/issues)  :)
Read documentation here: http://axe.rtfd.org
"""

from setuptools import setup

setup(
    name="Axe",
    version='0.0.4',
    author="Ju Lin",
    author_email="soasme@gmail.com",
    description="An Extendable Python Web Framework",
    long_description=__doc__,
    license="MIT License",
    keywords="Web frameword",
    url="https://github.com/soasme/axe",
    packages=['axe'],
    classifiers=[
        "Development Status :: 4 - Beta",
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        "License :: OSI Approved :: MIT License",
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
