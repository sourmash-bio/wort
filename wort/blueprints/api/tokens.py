from flask import jsonify, g, Blueprint

api = Blueprint("api", __name__)

from wort.ext import basic_auth, token_auth, db


@api.route("/tokens", methods=["POST"])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_token(expires_in=86400)
    db.session.commit()
    return jsonify({"token": token})


@api.route("/tokens", methods=["DELETE"])
@token_auth.login_required
def revoke_token():
    g.current_user.get_token()
    db.session.commit()
    return "", 204
