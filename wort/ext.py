from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from cachelib import RedisCache

login = LoginManager()

db = SQLAlchemy()
migrate = Migrate()

cache = RedisCache(host="redis")
