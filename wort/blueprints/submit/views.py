import gzip
from io import BytesIO
import shutil

from flask import Blueprint, request, jsonify, g
from wort.blueprints.api.auth import token_auth


submit = Blueprint("submit", __name__, template_folder="templates")


@token_auth.login_required
def submit_sigs(public_db, dataset_id):

    if public_db not in ("sra", "img"):
        return "Database not supported", 404

    import boto3

    conn = boto3.client("s3")

    username = g.current_user.username
    key = f"{username}/{dataset_id}.sig"

    file = request.files["file"]
    if any(f == file.content_type for f in ("application/gzip", "application/x-gzip")):
        # if it's already gzipped, don't compress it
        compressed = file.stream
    else:
        compressed_fp = BytesIO()
        with gzip.GzipFile(fileobj=compressed_fp, mode="wb") as gz:
            shutil.copyfileobj(file.stream, gz)
        compressed = compressed_fp.getvalue()

    conn.put_object(
        Body=compressed,
        Bucket=f"wort-submitted-{public_db}",
        Key=key,
        ContentType="application/json",
        ContentEncoding="gzip",
    )

    return jsonify({"status": "Signature accepted"}), 202
