import connexion

from celery import Celery

from wort.blueprints.compute import compute
from wort.blueprints.submit import submit
from wort.blueprints.viewer import viewer
from wort.blueprints.api import api
from wort.blueprints.errors import errors

from wort.ext import login, db, migrate

CELERY_TASK_LIST = ["wort.blueprints.compute.tasks"]


def create_celery_app(app=None):
    """
    Create a new Celery object and tie together the Celery config to the app's
    config. Wrap all tasks in the context of the application.
    :param app: Flask app
    :return: Celery app
    """
    app = app or create_app().app

    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        include=CELERY_TASK_LIST,
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_app(settings_override=None):
    """
    Create a Flask application using the app factory pattern.
    :param settings_override: Override settings
    :return: Flask app
    """
    app = connexion.App(__name__, swagger_ui=True, swagger_json=True)
    app.add_api("api.yaml")

    app.app.config.from_object("config.settings")

    if settings_override:
        app.config.update(settings_override)

    blueprints(app.app)
    extensions(app.app)

    return app


def blueprints(app):
    app.register_blueprint(errors)
    app.register_blueprint(compute)
    app.register_blueprint(submit)
    app.register_blueprint(viewer)
    app.register_blueprint(api)


def extensions(app):
    """
    Register 0 or more extensions (mutates the app passed in).
    :param app: Flask application instance
    :return: None
    """
    login.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    return None
