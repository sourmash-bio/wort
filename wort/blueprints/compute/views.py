import csv

from flask import Blueprint, current_app, jsonify, render_template, url_for
import requests

from wort.ext import db
from wort.models import Dataset, Database
import io

compute = Blueprint("compute", __name__, template_folder="templates")


TRACE_DATA_URL = 'https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term={dataset}'
# TRACE_DATA_URL = 'https://www.ebi.ac.uk/ena/portal/api/filereport?result=read_run&accession=SRR1620998&fields=run_accession,fastq_ftp,fastq_md5,fastq_bytes,library_layout,read_count,base_count&format=tsv'
# TRACE_DATA_URL = 'https://www.ebi.ac.uk/ena/portal/api/filereport?result=read_run&accession={run}&fields=run_accession,fastq_ftp,fastq_md5,fastq_bytes,library_layout,read_count,base_count&format=tsv'
# ena_file_report = 'https://www.ebi.ac.uk/ena/portal/api/filereport?result=read_run&accession={run}&fields=run_accession,fastq_ftp,fastq_md5,fastq_bytes,library_layout,read_count,base_count&format=tsv'
# ena_file_report = 'https://www.ebi.ac.uk/ena/portal/api/filereport?result=read_run&accession={run}&fields=run_accession,fastq_ftp,fastq_md5,fastq_bytes,library_layout,read_count,base_count&format=tsv'


def compute_sra(sra_id, recompute=False):
    from . import tasks

    dataset = Dataset.query.filter_by(id=sra_id).first()
    if dataset is None:
        # In compute_sra when dataset is None
        # resp = requests.get(ena_file_report.format(run=sra_id), timeout=30)
        resp = requests.get(TRACE_DATA_URL.format(run=sra_id), timeout=30)
        resp.raise_for_status()
        tsv = resp.text.strip()
        if not tsv or tsv.splitlines()[0].startswith("error"):
            return jsonify({"status": "Not found in ENA"}), 404
        reader = csv.DictReader(io.StringIO(tsv), delimiter="\t")
        rows = list(reader)
        if not rows:
            return jsonify({"status": "Not found in ENA"}), 404
        row = rows[0]

        bytes_total = 0
        if row.get("fastq_bytes"):
            bytes_total = sum(int(x) for x in row["fastq_bytes"].split(";") if x)
        size_MB = int((bytes_total + 1_000_000 - 1) / 1_000_000) if bytes_total else None

        # Set database_id to ENA to indicate source of FASTQs
        dataset = Dataset(id=row["run_accession"], database_id="ENA", size_MB=size_MB, ipfs=None)
        db.session.add(dataset)
        db.session.commit()



        # # We don't have information about it, query SRA and insert it
        # # TODO: deal with errors
        # #db = Database.query.filter_by(id="SRA").first()
        # #rawdata = requests.get(db.metadata_link.format(dataset=sra_id)).content.decode("utf-8")
        # rawdata = requests.get(TRACE_DATA_URL.format(dataset=sra_id)).content.decode("utf-8")
        # data = list(csv.DictReader(rawdata.splitlines(), delimiter=","))
        # row = data[0]
        # dataset = Dataset(id=row["Run"], database_id="SRA", size_MB=row["size_MB"], ipfs=None)
        # db.session.add(dataset)
        # db.session.commit()

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

            key_path = f"sigs/{sra_id}.sig"
            try:
                # obj = s3.Object("wort-sra", key_path)
                obj = s3.Object("branchwater", key_path)
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

    # Choose computation path based on dataset source
    if dataset.database_id == "ENA":
        task = tasks.compute_ena.apply_async(args=[sra_id], queue=queue)
    else:
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
