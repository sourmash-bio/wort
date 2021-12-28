import connexion
from celery import Celery
from flask import current_app, jsonify, render_template, url_for
from sqlalchemy import func

from wort.blueprints.auth import auth
from wort.blueprints.compute import compute
from wort.blueprints.errors import errors
from wort.blueprints.submit import submit
from wort.blueprints.viewer import viewer
from wort.ext import cache, db, login, migrate
from wort.models import Database, Dataset

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
    app = connexion.App(__name__, options={"swagger_ui": True, "serve_spec": True})
    app.add_api("api.yaml")

    app.app.config.from_object("config.settings")

    if settings_override:
        app.config.update(settings_override)

    blueprints(app.app)
    extensions(app.app)

    @app.route("/about/")
    def about():
        return render_template("about.html")

    @app.route("/")
    def index():
        n_datasets = current_app.cache.get(f"meta/n_datasets")
        if n_datasets is None:
            n_datasets = Dataset.query.count()
            current_app.cache.set(f"meta/n_datasets", n_datasets, timeout=86400)

        size_TB = current_app.cache.get(f"meta/size_TB")
        if size_TB is None:
            size_MB = Dataset.query.with_entities(func.sum(Dataset.size_MB)).first()[0]
            size_TB = size_MB / 1000. / 1000.
            current_app.cache.set(f"meta/size_TB", size_TB, timeout=86400)

        return render_template("index.html", n_datasets=n_datasets, size_TB=size_TB)

    @app.route("/view/")
    def view_base():
        return render_template("view_base.html")

    @app.route("/view/<public_db>/<dataset_id>/")
    def view(public_db=None, dataset_id=None):
        dataset_info = current_app.cache.get(f"{public_db}/{dataset_id}")

        if dataset_info is None:
            # Not in cache, let's check DB
            dataset = Dataset.query.filter_by(id=dataset_id).first()

            if dataset is not None:
                # Found a hit in DB
                dataset_info = {}
                #if dataset.ipfs is not None:
                    # only show if IPFS hash is available
                if 1:
                    dataset_info["name"] = dataset_id.upper()
                    dataset_info["db"] = public_db.upper()
                    dataset_info["link"] = f"/v1/view/{public_db}/{dataset_id}"
                    dataset_info["metadata"] = dataset.database.metadata_link.format(dataset=dataset_id)
                    dataset_info["ipfs"] = dataset.ipfs
                    # let's update cache
                    current_app.cache.set(f"{public_db}/{dataset_id}", dataset_info)

        return render_template("view.html", dataset=dataset_info)

    return app


def blueprints(app):
    app.register_blueprint(errors)
    app.register_blueprint(compute)
    app.register_blueprint(submit)
    app.register_blueprint(viewer)
    app.register_blueprint(auth)


def extensions(app):
    """
    Register 0 or more extensions (mutates the app passed in).
    :param app: Flask application instance
    :return: None
    """
    login.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    app.cache = cache

    return None
