from flask import Blueprint, current_app, jsonify, redirect, render_template

viewer = Blueprint("viewer", __name__, template_folder="templates")


# @viewer.route("/view/<db>/<dataset_id>")
def view_s3(public_db, dataset_id):

    if public_db not in ("sra", "img", "genomes"):
        return "Database not supported", 404

    import boto3

    conn = boto3.client("s3")

    key = f"sigs/{dataset_id}.sig"

    params = {
        "Bucket": f"wort-{public_db}",
        "Key": key,
        "ResponseContentType": "application/json",
        "ResponseContentEncoding": "gzip",
    }

    url = conn.generate_presigned_url("get_object", Params=params, ExpiresIn=100)

    return redirect(url)

# @viewer.route("/view/<db>/<dataset_id>")
def view(public_db, dataset_id):

    if public_db not in ("sra", "img", "genomes"):
        return "Database not supported", 404

    dataset_info = current_app.cache.get(f"{public_db}/{dataset_id}")

    if dataset_info is None:
        from wort.models import Dataset

        # Not in cache, let's check DB
        dataset = Dataset.query.filter_by(id=dataset_id).first()

        if dataset is not None:
            # Found a hit in DB
            if dataset.ipfs is not None and public_db == "genomes":
                return redirect(f"https://cloudflare-ipfs.com/ipfs/{dataset.ipfs}")
            else:
                # SRA/IMG IPFS links are unreliable, default to s3
                return view_s3(public_db, dataset_id)
    else:
        # Found in cache, redirect
        return redirect(f"https://cloudflare-ipfs.com/ipfs/{dataset_info['ipfs']}")

    return "Dataset not found", 404
