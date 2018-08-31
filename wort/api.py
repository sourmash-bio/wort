import os

from flask import jsonify, redirect


def compute_sra(sra_id):
    from . import tasks

    task = tasks.compute.delay(sra_id)
    return jsonify({"task_id": task.id}), 202


def view_s3(public_db, dataset_id):
    if public_db not in ("sra", "img"):
        return "Database not supported", 404

    import boto3

    conn = boto3.client("s3")

    key = f"sigs/{dataset_id}.sig"
    # TODO: we don't really need this, I just copied the signatures improperly
    # to the bucket...
    if public_db == "img":
        key = f"{dataset_id}.sig"

    url = conn.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": f"wort-{public_db}",
            "Key": key,
            "ResponseContentType": "application/json",
            # 'ResponseContentEncoding': 'gzip',
        },
        ExpiresIn=100,
    )

    return redirect(url)
