import time

from flask import Blueprint, current_app, g, jsonify
from werkzeug.exceptions import Unauthorized

from wort.ext import db
from wort.models import User

from .errors import error_response

auth = Blueprint("auth", __name__)


def basic_auth(username, password, required_scopes=None):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return False

    if user.check_password(password):
        g.current_user = user
        return {"sub": username, "scope": ""}
    else:
        return None


def get_token():
    token = g.current_user.get_token(expires_in=86400)
    db.session.commit()
    return token


def verify_token(token):
    g.current_user = User.check_token(token) if token else None
    if g.current_user is not None:
        return {"sub": g.current_user.username, "scope": ""}


def revoke_token():
    g.current_user.get_token()
    db.session.commit()
    return jsonify({"status": "OK"}), 204
