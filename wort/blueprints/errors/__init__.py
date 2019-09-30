from flask import Blueprint

from . import handlers

errors = Blueprint("errors", __name__)
