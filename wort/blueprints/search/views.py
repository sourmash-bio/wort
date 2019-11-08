from base64 import b64encode
import os

from flask import Blueprint, render_template, jsonify, url_for, current_app

search = Blueprint("search", __name__, template_folder="templates")


def search_dispatch(index, signature):
    import boto3
    import botocore

    from . import tasks

    """
    s3 = boto3.resource("s3")

    key_path = os.path.join("sigs", sra_id + ".sig")

    is_computed = current_app.cache.get("wort-sra/" + key_path)
    if is_computed:
        return jsonify({"status": "Signature already calculated"}), 202

    try:
        s3.Object("wort-sra", key_path).load()
        current_app.cache.set("wort-sra/" + key_path, True, timeout=0)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            pass  # Object does not exist, let's compute it later
        else:
            # Something else has gone wrong
            raise
    else:
        # The key already exists
        return jsonify({"status": "Signature already calculated"}), 202

    """
    # TODO: save signature to S3, send only link?
    task = tasks.search_genbank.apply_async(
        args=[b64encode(signature.read()).decode("ascii")],
        queue='search'
    )
    return jsonify({"status": "Submitted", "task_id": task.id}), 202
