from wort.app import create_app, create_celery_app
from wort.ext import db
from wort.models import Task, User

app = create_app().app
celery = create_celery_app(app)


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Task": Task}
