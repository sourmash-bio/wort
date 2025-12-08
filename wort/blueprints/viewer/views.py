from flask import Blueprint, current_app, jsonify, redirect, render_template

viewer = Blueprint("viewer", __name__, template_folder="templates")


# @viewer.route("/view/<db>/<dataset_id>")
def view_s3(public_db, dataset_id):

    if public_db not in ("sra", "img", "genomes"):
        return "Database not supported", 404

    import boto3

    conn = boto3.client(
        service_name="s3",
        endpoint_url=current_app.config["SIG_STORAGE_ENDPOINT_URL"],
        aws_access_key_id=current_app.config["SIG_STORAGE_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["SIG_STORAGE_SECRET_ACCESS_KEY"],
        region_name="auto",
    )

    key = f"sigs/{dataset_id}.sig"

    params = {
        "Bucket": f"wort-{public_db}",
        "Key": key,
        "ResponseContentType": "application/json",
        "ResponseContentEncoding": "gzip",
        "ResponseContentDisposition": f'attachment; filename="{dataset_id}.sig"',
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
            #if dataset.ipfs is not None and public_db == "genomes":
            #    return redirect(f"https://cloudflare-ipfs.com/ipfs/{dataset.ipfs}")
            #else:
            #    # could do this if egress charges were not so high...
            return view_s3(public_db, dataset_id)
            #return redirect(f"https://farm.cse.ucdavis.edu/~irber/wort-{public_db}/sigs/{dataset_id}.sig")
    else:
        # Found in cache, redirect
        #return redirect(f"https://cloudflare-ipfs.com/ipfs/{dataset_info['ipfs']}")
        return view_s3(public_db, dataset_id)
        #return redirect(f"https://farm.cse.ucdavis.edu/~irber/wort-{public_db}/sigs/{dataset_id}.sig")

    return "Dataset not found", 404
