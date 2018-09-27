from flask import Blueprint, render_template, jsonify, redirect

viewer = Blueprint("viewer", __name__, template_folder="templates")


# @viewer.route("/view/<db>/<dataset_id>")
def view_s3(public_db, dataset_id):

    if public_db not in ("sra", "img"):
        return "Database not supported", 404

    import boto3

    conn = boto3.client("s3")

    key = f"sigs/{dataset_id}.sig"

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
