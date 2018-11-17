from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.contrib.cache import RedisCache

login = LoginManager()

db = SQLAlchemy()
migrate = Migrate()

cache = RedisCache(host="redis")
