import connexion
from celery import Celery
from flask import current_app, jsonify, render_template, url_for

from wort.blueprints.auth import auth
from wort.blueprints.compute import compute
from wort.blueprints.errors import errors
from wort.blueprints.submit import submit
from wort.blueprints.viewer import viewer
from wort.ext import cache, db, login, migrate

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
        return render_template("index.html")

    @app.route("/view/")
    def view_base():
        return render_template("view_base.html")

    @app.route("/view/<public_db>/<dataset_id>/")
    def view(public_db=None, dataset_id=None):
        dataset = current_app.cache.get(f"wort-{public_db}/sigs/{dataset_id}.sig")
        if dataset:
            if isinstance(dataset, bool):
                # This was generated in the compute view, fix it to be a dict
                dataset = {}
                dataset["name"] = dataset_id.upper()
                dataset["db"] = public_db.upper()
                dataset["link"] = f"/v1/view/{public_db}/{dataset_id}"
                if public_db == "sra":
                    dataset[
                        "metadata"
                    ] = f"https://trace.ncbi.nlm.nih.gov/Traces/sra/?run={dataset_id.upper()}"
                elif public_db == "img":
                    dataset[
                        "metadata"
                    ] = f"https://img.jgi.doe.gov/cgi-bin/m/main.cgi?section=TaxonDetail&page=taxonDetail&taxon_oid={dataset_id}"
                current_app.cache.set(f"wort-{public_db}/sigs/{dataset_id}.sig", dataset)
        else:
            # TODO: is it really missing, or cache wasn't set up properly?
            # this is especially true for IMG, since there is no point in code
            # setting the cache for it.
            #
            # S3 check for file is one option, but very easy to get a very large
            # bill if someone start requesting spurious datasets...
            pass

        return render_template("view.html", dataset=dataset)

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
