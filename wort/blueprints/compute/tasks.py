
import gzip
import os
import shutil
from io import BytesIO
import shlex
from subprocess import run, CalledProcessError
from tempfile import NamedTemporaryFile

from celery.exceptions import Ignore

from wort.app import create_celery_app

celery = create_celery_app()


class WorkerRunError(Exception):
    pass


@celery.task
def compute(sra_id):
    import boto3
    import botocore

    conn = boto3.client("s3")
    s3 = boto3.resource("s3")

    key_path = os.path.join("sigs", sra_id + ".sig")
    try:
        # s3.Object("wort-sra", key_path).load()
        s3.Object("branchwater", key_path).load()
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            pass  # Object does not exist, let's compute it later
        else:
            # Something else has gone wrong
            raise

    else:
        # The key already exists
        return

    with NamedTemporaryFile("w+b") as f:
        try:
            result = run(
                "set -euo pipefail; "
                f"fastq-dump --disable-multithreading --fasta 0 --skip-technical --readids --read-filter pass --dumpbase --split-spot --clip -Z {sra_id} | "
                "sourmash compute -k 21,31,51 "
                "  --scaled 1000 "
                "  --track-abundance "
                f"  --name {sra_id} "
                f"  -o {f.name} "
                "  - ",
                shell=True, capture_output=True, check=True,
                executable="/bin/bash",
            )
        except CalledProcessError as e:
            if e.returncode == 3:
                # Happens when fastq-dump can't find an accession
                # (might have been removed, redacted, or never uploaded,
                #  and in some cases need dbGaP permission, like SRR27017016)
                # stop further processing.
                return

            # We ignore SIGPIPE, since it is informational (and makes sense,
            # it happens because `head` is closed and `fastq-dump` can't pipe
            # its output anymore. More details:
            # http://www.pixelbeat.org/programming/sigpipe_handling.html
            elif e.returncode != 141:
                raise e
        else:
            result = result

        # if file is empty, consider it an error and sift
        # through logs later to figure out better error control
        if os.stat(f.name).st_size == 0:
            raise WorkerRunError(result.stdout)

        f.seek(0)

        compressed_fp = BytesIO()
        with gzip.GzipFile(fileobj=compressed_fp, mode="wb") as gz:
            shutil.copyfileobj(f, gz)

        # conn.put_object(
        #     Body=compressed_fp.getvalue(),
        #     Bucket="wort-sra",
        #     Key=key_path,
        #     ContentType="application/json",
        #     ContentEncoding="gzip",
        # )

        conn.put_object(
            Body=compressed_fp.getvalue(),
            Bucket="branchwater",
            Key=key_path,
            ContentType="application/json",
            ContentEncoding="gzip",
        )


@celery.task
def compute_ena(run_accession):
    """
    Compute sourmash signature by streaming ENA-hosted FASTQ files for the run.
    Mirrors the sourmash parameters used for SRA-based compute but without SRA-specific
    clipping/filters. The resulting signature is uploaded to the same S3 bucket
    under sigs/{run_accession}.sig
    """
    import boto3
    import botocore
    import requests
    import csv
    import io as _io

    conn = boto3.client("s3")
    s3 = boto3.resource("s3")

    key_path = os.path.join("sigs", run_accession + ".sig")

    # If already present, skip
    try:
        s3.Object("branchwater", key_path).load()
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            pass
        else:
            raise
    else:
        return

    # Discover ENA FASTQ URLs
    api = (
        "https://www.ebi.ac.uk/ena/portal/api/filereport?"
        f"result=read_run&accession={run_accession}&"
        "fields=run_accession,fastq_ftp,library_layout&format=tsv"
    )
    resp = requests.get(api, timeout=60)
    resp.raise_for_status()
    tsv = resp.text.strip()
    if not tsv or tsv.splitlines()[0].startswith("error"):
        # Nothing to do
        return

    reader = csv.DictReader(_io.StringIO(tsv), delimiter="\t")
    rows = list(reader)
    if not rows or not rows[0].get("fastq_ftp"):
        return

    fastq_ftp = rows[0]["fastq_ftp"]
    files = [f for f in fastq_ftp.split(";") if f]

    # Build bash loop to stream all files in order (R1 then R2 if present)
    # ENA provides FTP paths; use HTTPS with host prefix
    urls = " ".join([shlex.quote("https://" + f) for f in files])

    with NamedTemporaryFile("w+b") as f:
        try:
            cmd = (
                "set -euo pipefail; "
                f"for u in {urls}; do curl -sL \"$u\" | zcat; done | "
                "sourmash compute -k 21,31,51 "
                "  --scaled 1000 "
                "  --track-abundance "
                f"  --name {shlex.quote(run_accession + '_ENA_raw')} "
                f"  -o {f.name} "
                "  - "
            )
            result = run(cmd, shell=True, capture_output=True, check=True, executable="/bin/bash")
        except CalledProcessError as e:
            # Allow SIGPIPE, otherwise raise
            if e.returncode != 141:
                raise e
        else:
            result = result

        if os.stat(f.name).st_size == 0:
            raise WorkerRunError(result.stdout)

        f.seek(0)
        compressed_fp = BytesIO()
        with gzip.GzipFile(fileobj=compressed_fp, mode="wb") as gz:
            shutil.copyfileobj(f, gz)

        conn.put_object(
            Body=compressed_fp.getvalue(),
            Bucket="branchwater",
            Key=key_path,
            ContentType="application/json",
            ContentEncoding="gzip",
        )


@celery.task
def compute_genomes(accession, path, name):
    import boto3
    import botocore

    conn = boto3.client("s3")
    s3 = boto3.resource("s3")

    key_path = os.path.join("sigs", accession + ".sig")
    try:
        # s3.Object("wort-genomes", key_path).load()
        s3.Object("branchwater-genomes", key_path).load()
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            pass  # Object does not exist, let's compute it later
        else:
            # Something else has gone wrong
            raise

    else:
        # The key already exists
        return

    with NamedTemporaryFile("w+b") as f:
        try:
            result = run(
                "set -euo pipefail; "
                "sourmash compute -k 21,31,51 "
                "  --scaled 1000 "
                "  --track-abundance "
                f"  --name {shlex.quote(name)} "
                f"  -o {f.name} "
                f"  <(curl {path} | zcat)",
                shell=True, capture_output=True, check=True,
                executable="/bin/bash",
            )
        except CalledProcessError as e:
            # We ignore SIGPIPE, since it is informational (and makes sense,
            # it happens because `head` is closed and `fastq-dump` can't pipe
            # its output anymore. More details:
            # http://www.pixelbeat.org/programming/sigpipe_handling.html
            if e.returncode != 141:
                raise e
        else:
            result = result

        # if file is empty, consider it an error and sift
        # through logs later to figure out better error control
        if os.stat(f.name).st_size == 0:
            raise WorkerRunError(result.stdout)

        f.seek(0)

        compressed_fp = BytesIO()
        with gzip.GzipFile(fileobj=compressed_fp, mode="wb") as gz:
            shutil.copyfileobj(f, gz)

        conn.put_object(
            Body=compressed_fp.getvalue(),
            Bucket="branchwater-genomes",
            Key=key_path,
            ContentType="application/json",
            ContentEncoding="gzip",
        )
