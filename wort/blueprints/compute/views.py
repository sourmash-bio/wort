from flask import Blueprint, render_template, jsonify, url_for

compute = Blueprint('compute', __name__, template_folder='templates')

from wort.blueprints.api.auth import token_auth


@compute.route('/')
def index():
    return jsonify({'key': "Hello World"})


@compute.route('/compute/sra/<sra_id>', methods=['POST'])
@token_auth.login_required
def compute_sra(sra_id):
    from . import tasks

    task = tasks.compute.delay(sra_id)
    return jsonify({'task_id': task.id}), 202
