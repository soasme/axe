Axe
========

[![Build Status](https://travis-ci.org/soasme/axe.svg?branch=master)](https://travis-ci.org/soasme/axe)
[Documentation](http://axe.readthedocs.org/en/latest/)

### What is Axe?

Axe is an extremely extendable web framework for Python based on `Werkzeug`.
It help developer keep project easy to extend and test when project grows.

Unlike Flask, there is no **Thread-Local** variables like `flask.request`, `flask.g`.
All variable are injected into view function through function name inspired by `py.test fixture`.

**Warning**: It's still experimental and has many buggy.

### Example

```python
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
```

### How to run tests?

Run All tests:

    $ tox

Run single case:

    $ py.test tests/test_basic.py -k test_get_index

### Where can I get help?

You can ask any question in [Github Issue](https://github.com/soasme/axe/issues)  :)
