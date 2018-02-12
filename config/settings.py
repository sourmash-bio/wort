import os
basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", 'insecuredev')

# Celery.
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_REDIS_MAX_CONNECTIONS = 5

BROKER_HEARTBEAT = None

SQLALCHEMY_DATABASE_URI = os.path.expandvars(os.environ.get('DATABASE_URL',
                                         'sqlite:///' + os.path.join(basedir, 'app.db')))
SQLALCHEMY_TRACK_MODIFICATIONS = False
