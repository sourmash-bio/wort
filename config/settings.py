import os

basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", "insecuredev")

# Celery SQS
result_backend = "celery_s3.backends.S3Backend"

CELERY_S3_BACKEND_SETTINGS = {
    "aws_access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
    "aws_secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
    "bucket": "wort-results",
}

task_serializer = "json"
accept_content = ["json", "yaml"]
result_serializer = "json"

worker_enable_remote_control = False
worker_send_tasks_events = False

CELERY_enable_utc = True
worker_disable_rate_limits = True

CELERY_broker_url = "sqs://"
broker_transport_options = {
    "queue_name_prefix": "wort-",
    "visibility_timeout": 3600,  # seconds
    "wait_time_seconds": 20,  # Long polling
    "polling_interval": 10,  # check queue every 10 seconds
}

broker_heartbeat = None

SQLALCHEMY_DATABASE_URI = os.path.expandvars(
    os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "app.db"))
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
