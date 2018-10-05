import os

from flask import Blueprint, render_template, jsonify, url_for

compute = Blueprint("compute", __name__, template_folder="templates")

from wort.blueprints.api.auth import token_auth


# @compute.route("/compute/sra/<sra_id>", methods=["POST"])
@token_auth.login_required
def compute_sra(sra_id):
    import boto3
    import botocore

    from . import tasks

    s3 = boto3.resource("s3")

    key_path = os.path.join("sigs", sra_id + ".sig")
    try:
        s3.Object("wort-sra", key_path).load()
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            pass  # Object does not exist, let's compute it later
        else:
            # Something else has gone wrong
            raise
    else:
        # The key already exists
        return jsonify({"status": "Signature already calculated"}), 202

    task = tasks.compute.delay(sra_id)
    return jsonify({"status": "Submitted", "task_id": task.id}), 202
