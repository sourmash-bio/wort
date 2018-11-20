import gzip
from io import BytesIO
import shutil

from flask import Blueprint, request, jsonify, g


submit = Blueprint("submit", __name__, template_folder="templates")


def submit_sigs(public_db, dataset_id):

    if public_db not in ("sra", "img"):
        return "Database not supported", 404

    import boto3

    conn = boto3.client("s3")

    username = g.current_user.username
    key = f"{username}/{dataset_id}.sig"

    file = request.files["file"]
    compressed_fp = BytesIO()
    # TODO: if it's already gzipped, don't compress it
    with gzip.GzipFile(fileobj=compressed_fp, mode="wb") as gz:
        shutil.copyfileobj(file.stream, gz)

    conn.put_object(
        Body=compressed_fp.getvalue(),
        Bucket=f"wort-submitted-{public_db}",
        Key=key,
        ContentType="application/json",
        ContentEncoding="gzip",
    )

    return jsonify({"status": "Signature accepted"}), 202
