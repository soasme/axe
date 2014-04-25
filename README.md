Axe
========

[![Build Status](https://travis-ci.org/soasme/axe.svg?branch=master)](https://travis-ci.org/soasme/axe)

### What is Axe?

Axe is an extremely extendable web framework for Python based on `Werkzeug`. It help developer keep project easy to extend and test when project grows bigger and bigger.

* IoC

Unlike Flask, there is no **Thread-Local** variables like `flask.request`, `flask.g`.
All variable are injected into view function through function name inspired by `py.test fixture`.

* Concurrent

.

**Warning**: It's still experimental and has many buggy.

### Example

```python
from axe import Axe, jsonify
app = Axe()

@app.ext
def login(request):
    token = request.headers['Authorization']
    user = Account.get_from_token(token)
    if not user:
        abort(403)
    return user

def index(login):
    return jsonify({'id': login.id, 'expire': login.expire})

app.build({
    '/': index
})

if __name__ == '__main__':
    app.run()
```

### How to run tests?

Run All tests:

    $ tox

Run single case:

    $ py.test tests/test_basic.py -k test_get_index

### Where can I get help?

You can ask any question in [Github Issue](https://github.com/soasme/axe/issues)  :)
