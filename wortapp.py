from wort.app import create_app
from wort.ext import db
from wort.models import User, Task

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task}
