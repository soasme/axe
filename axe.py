import os
import logging

from flask import Flask
from flask_apscheduler import APScheduler
from prometheus_client import make_wsgi_app
from werkzeug.wsgi import DispatcherMiddleware
from wsgiref.simple_server import make_server

logger = logging.getLogger('axe')

def count():
    logger.warning('count: %s' % 1)

def create_app():
    app = Flask(__name__)

    if 'AXE_CONFIG' in os.environ:
        app.config.from_envvar('AXE_CONFIG')
    else:
        logger.warning('Missing config: AXE_CONFIG.')

    app.config.update({
        'SCHEDULER_API_ENABLED': True,
        'JOBS': [
            {
                'func': count,
                'trigger': 'interval',
                'seconds': 3,
                'id': 'count',
            }
        ]
    })
    scheduler = APScheduler()
    scheduler.init_app(app)

    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': make_wsgi_app()
    })

    return app

def run_app():
    app = create_app()

    port = int(os.environ.get('PORT') or 9102)
    httpd = make_server('', port, app)

    logger.info('Axe started background scheduler.')
    app.apscheduler.start()

    logger.info('Axe started listening on :%d' % port)
    httpd.serve_forever()

if __name__ == '__main__':
    run_app()
