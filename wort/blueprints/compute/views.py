import csv
import os

from flask import Blueprint, current_app, jsonify, render_template, url_for
import requests

from wort.ext import db
from wort.models import Dataset, Database

compute = Blueprint("compute", __name__, template_folder="templates")


TRACE_DATA_URL = 'https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term={dataset}'


def compute_sra(sra_id):
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

    is_computed = dataset.ipfs is not None
    if is_computed:
        return jsonify({"status": "Signature already calculated"}), 202

    # Not computed yet, send to proper queue
    if dataset.size_MB <= 300:
        queue = "compute_small"
    elif dataset.size_MB > 300 and dataset.size_MB < 1600:
        queue = "compute_medium"
    else:
        queue = "compute_large"

    task = tasks.compute.apply_async(args=[sra_id], queue=queue)
    return jsonify({"status": "Submitted", "task_id": task.id}), 202
