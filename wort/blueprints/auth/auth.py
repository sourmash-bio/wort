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

    g.current_user = user
    if user.check_password(password):
        return {"sub": username, "scope": ""}
    else:
        return None


def generate_token():
    timestamp = _current_timestamp()
    payload = {
        "iss": JWT_ISSUER,
        "iat": int(timestamp),
        "exp": int(timestamp + JWT_LIFETIME_SECONDS),
        "sub": str(g.current_user),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise Unauthorized from e


def _current_timestamp():
    return int(time.time())
