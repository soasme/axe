# -*- coding: utf-8 -*-

def index():
    return 'Index'

def hello(query):
    return 'Hello World: %s' % query.get('name', '[Anon]')

from taxe import Taxe
app = Taxe()
app.build({
    '/': index,
    '/hello': hello,
})
