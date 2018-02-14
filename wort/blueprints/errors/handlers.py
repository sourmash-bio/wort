from flask import request

from . import errors
from wort.ext import db
from wort.blueprints.api.errors import error_response as api_error_response


def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


@errors.errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    return 'Not Found', 404


@errors.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return 'internal server error', 500
