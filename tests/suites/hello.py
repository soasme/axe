# -*- coding: utf-8 -*-

def index():
    return 'Index'

def hello(query):
    return 'Hello World: %s' % query.get('name', '[Anon]')

from axe import Axe
app = Axe()
app.build({
    '/': index,
    '/hello': hello,
})

if __name__ == '__main__':
    app.run_simple(host='127.0.0.1', port=8384)
