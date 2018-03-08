import os
basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", 'insecuredev')

# Celery SQS
CELERY_RESULT_BACKEND = 'celery_s3.backends.S3Backend'

CELERY_S3_BACKEND_SETTINGS = {
    'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID'],
    'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY'],
    'bucket': 'wort-results',
}

CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json', 'yaml']
CELERY_RESULT_SERIALIZER = 'json'

CELERY_ENABLE_REMOTE_CONTROL = False
CELERY_SEND_EVENTS = False

CELERY_ENABLE_UTC = True
CELERY_DISABLE_RATE_LIMITS = True

CELERY_BROKER_URL = 'sqs://'
BROKER_TRANSPORT_OPTIONS = {
    'queue_name_prefix': 'wort-',
    'visibility_timeout': 3600,  # seconds
    'wait_time_seconds': 20,  # Long polling
    'polling_interval': 10,  # check queue every 10 seconds
}

BROKER_HEARTBEAT = None

SQLALCHEMY_DATABASE_URI = os.path.expandvars(
    os.environ.get('DATABASE_URL',
                   'sqlite:///' + os.path.join(basedir, 'app.db')))
SQLALCHEMY_TRACK_MODIFICATIONS = False
