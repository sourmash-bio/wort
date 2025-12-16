import os

basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", "insecuredev")

SQLALCHEMY_DATABASE_URI = os.path.expandvars(
    os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "app.db"))
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

SIG_STORAGE_ACCESS_KEY_ID = os.environ.get("SIG_STORAGE_ACCESS_KEY_ID")
SIG_STORAGE_SECRET_ACCESS_KEY = os.environ.get("SIG_STORAGE_SECRET_ACCESS_KEY")
SIG_STORAGE_ENDPOINT_URL = os.environ.get("SIG_STORAGE_ENDPOINT_URL")

# Celery SQS
CELERY_CONFIG = {
    "result_backend": "celery.backends.s3.S3Backend",

    "s3_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
    "s3_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
    "s3_bucket": "wort-results",

    "task_serializer": "json",
    "accept_content": ["json", "yaml"],
    "result_serializer": "json",

    "worker_enable_remote_control": False,
    "worker_send_tasks_events": False,

    "enable_utc": True,
    "worker_disable_rate_limits": True,

    "broker_url": "sqs://",
    "broker_transport_options": {
        "queue_name_prefix": "wort-",
        "visibility_timeout": 3600,  # seconds
        "wait_time_seconds": 20,  # Long polling
        "polling_interval": 10,  # check queue every 10 seconds
    },

    "broker_heartbeat": None,
}
