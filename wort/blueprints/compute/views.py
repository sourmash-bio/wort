import csv
import os
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, url_for
import requests

from wort.ext import db
from wort.models import Dataset, Database

compute = Blueprint("compute", __name__, template_folder="templates")


TRACE_DATA_URL = 'https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term={dataset}'


def compute_sra(sra_id, recompute=False):
    from . import tasks

    dataset = Dataset.query.filter_by(id=sra_id).first()
    if dataset is None:
        # We don't have information about it, query SRA and insert it
        # TODO: deal with errors
        #db = Database.query.filter_by(id="SRA").first()
        #rawdata = requests.get(db.metadata_link.format(dataset=sra_id)).content.decode("utf-8")
        rawdata = requests.get(TRACE_DATA_URL.format(dataset=sra_id)).content.decode("utf-8")
        data = list(csv.DictReader(rawdata.splitlines(), delimiter=","))
        row = data[0]
        dataset = Dataset(id=row["Run"], database_id="SRA", size_MB=row["size_MB"], ipfs=None)
        db.session.add(dataset)
        db.session.commit()

    up_to_date = False
    if not recompute:
        if dataset.computed is not None:
            up_to_date = True

        if dataset.computed is None:
            # check on S3 to see if it was computed and not updated in DB
            import boto3
            import botocore
            conn = boto3.client("s3")
            s3 = boto3.resource("s3")

            key_path = Path("sigs") / f"{sra_id}.sig"
            try:
                obj = s3.Object("wort-sra", key_path)
                obj.load()
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    pass  # Object does not exist yet
                else:
                    # Something else has gone wrong
                    raise
            else:
                # The key already exists, update compute field in DB
                dataset.computed = obj.last_modified
                db.session.add(dataset)
                db.session.commit()
                # Remove from cache, will be refreshed from DB next time
                # there is a view request for it
                current_app.cache.delete(f"sra/{sra_id}")

                up_to_date = True

    if up_to_date:
        return jsonify({"status": "Signature already calculated"}), 202

    if recompute:
        # Force recomputation of sketch,
        # clean status from DB and remove from cache
        dataset.computed = None
        db.session.add(dataset)
        db.session.commit()
        current_app.cache.delete(f"sra/{sra_id}")

    # Not computed yet, send to proper queue
    if dataset.size_MB <= 300:
        queue = "compute_small"
    elif dataset.size_MB > 300 and dataset.size_MB < 1600:
        queue = "compute_medium"
    else:
        queue = "compute_large"

    task = tasks.compute.apply_async(args=[sra_id], queue=queue)
    return jsonify({"status": "Submitted", "task_id": task.id}), 202


def compute_genomes(assembly_accession):
    from . import tasks

    dataset = Dataset.query.filter_by(id=assembly_accession).first()
    if dataset is None:
        # We don't have information about it, how to query GenBank/RefSeq for
        # info?
        return jsonify({"status": "Metadata not available"}), 404

    if dataset.computed is not None:
        return jsonify({"status": "Signature already calculated"}), 202

    # Not computed yet, send to proper queue
    if dataset.size_MB <= 300:
        queue = "compute_small"
    elif dataset.size_MB > 300 and dataset.size_MB < 1600:
        queue = "compute_medium"
    else:
        queue = "compute_large"

    task = tasks.compute_genomes.apply_async(
        args=[dataset.id, dataset.path, dataset.name],
        queue="genomes")
#        queue=queue)
    return jsonify({"status": "Submitted", "task_id": task.id}), 202
