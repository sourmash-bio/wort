from flask_login import LoginManager
from flask_httpauth import HTTPTokenAuth, HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

login = LoginManager()
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

db = SQLAlchemy()
migrate = Migrate()
