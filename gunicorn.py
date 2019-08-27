# -*- coding: utf-8 -*-

import os
import multiprocessing

bind = "127.0.0.1:5000"
# workers = multiprocessing.cpu_count() * 2 + 1   # workers=1
workers=1
# worker_class = "eventlet"   #pip install gunicorn[eventlet] 설치
reload = True
loglevel = "error"
preload_app = True
# worker_class = "sync"
# worker_connections = 1000
# timeout = 60*60*2
timeout = 60 * 60 * 5
errorlog = os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'logs'), 'server.log')

# CRITICAL: 'CRITICAL', ERROR: 'ERROR', WARNING: 'WARNING', INFO: 'INFO', DEBUG: 'DEBUG', NOTSET: 'NOTSET',
# LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'