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
