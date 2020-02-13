from flask import Blueprint, current_app, jsonify, redirect, render_template

viewer = Blueprint("viewer", __name__, template_folder="templates")


# @viewer.route("/view/<db>/<dataset_id>")
def view_s3(public_db, dataset_id):

    if public_db not in ("sra", "img"):
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


# @viewer.route("/info/<db>/<dataset_id>.json")
def info(public_db, dataset_id):
    dataset = current_app.cache.get(f"wort-{public_db}/sigs/{dataset_id}.sig")
    if dataset:
        dataset["name"] = dataset_id.upper()
        dataset["db"] = public_db.upper()
        dataset["link"] = f"/v1/view/{public_db}/{dataset_id}"
        if public_db == "sra":
            dataset[
                "metadata"
            ] = f"https://trace.ncbi.nlm.nih.gov/Traces/sra/?run={dataset_id.upper()}"
        elif public_db == "img":
            dataset[
                "metadata"
            ] = f"https://img.jgi.doe.gov/cgi-bin/m/main.cgi?section=TaxonDetail&page=taxonDetail&taxon_oid={dataset_id}"

    return jsonify(dataset), 200
