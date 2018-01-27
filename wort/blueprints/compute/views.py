from flask import Blueprint, render_template, jsonify, url_for

compute = Blueprint('compute', __name__, template_folder='templates')


@compute.route('/')
def index():
    return jsonify({'key': "Hello World"})


@compute.route('/compute/<sra_id>', methods=['POST'])
def compute_sra(sra_id):
    from . import tasks

    task = tasks.compute.delay(sra_id)
    return (jsonify({'task_id': task.id}), 202,
                  {'Location': url_for('compute.taskstatus', task_id=task.id)})


@compute.route('/status/<task_id>')
def taskstatus(task_id):
    from . import tasks

    task = tasks.compute.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)
