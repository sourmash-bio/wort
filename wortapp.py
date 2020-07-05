from wort.app import create_app
from wort.ext import db
from wort.models import Database, Dataset, User

app = create_app().app


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Database": Database, "Dataset": Dataset}
