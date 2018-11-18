import time

from flask import g, Blueprint
from jose import JWTError, jwt
from werkzeug.exceptions import Unauthorized

from wort.models import User

from .errors import error_response


auth = Blueprint("auth", __name__)


JWT_ISSUER = "org.oxli.wort"
JWT_SECRET = "change_this"
JWT_LIFETIME_SECONDS = 600
JWT_ALGORITHM = "HS256"


def basic_auth(username, password, required_scopes=None):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return False

    if user.check_password(password):
        g.current_user = user
        return {"sub": username, "scope": ""}
    else:
        return None


def generate_token():
    timestamp = _current_timestamp()
    payload = {
        "iss": JWT_ISSUER,
        "iat": int(timestamp),
        "exp": int(timestamp + JWT_LIFETIME_SECONDS),
        "sub": str(g.current_user.username),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        info = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = User.query.filter_by(username=info["sub"]).first()
        g.current_user = user
        return info
    except JWTError as e:
        raise Unauthorized from e


def _current_timestamp():
    return int(time.time())
