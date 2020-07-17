import gzip
import os
import shutil
from io import BytesIO
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile

from celery.exceptions import Ignore

from wort.app import create_celery_app

celery = create_celery_app()


@celery.task
def compute(sra_id):
    import boto3
    import botocore
    from snakemake import shell

    conn = boto3.client("s3")
    s3 = boto3.resource("s3")

    key_path = os.path.join("sigs", sra_id + ".sig")
    try:
        s3.Object("wort-sra", key_path).load()
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
            shell(
                "fastq-dump --disable-multithreading --fasta 0 --skip-technical --readids --read-filter pass --dumpbase --clip --split-e -Z {sra_id} | "
                "sourmash compute -k 21,31,51 "
                "  --scaled 1000 "
                "  --track-abundance "
                "  --name {sra_id} "
                "  -o {output} "
                "  - ".format(sra_id=sra_id, output=f.name)
            )
        except CalledProcessError as e:
            # We ignore SIGPIPE, since it is informational (and makes sense,
            # it happens because `head` is closed and `fastq-dump` can't pipe
            # its output anymore. More details:
            # http://www.pixelbeat.org/programming/sigpipe_handling.html
            if e.returncode != 141:
                raise e

        f.seek(0)

        compressed_fp = BytesIO()
        with gzip.GzipFile(fileobj=compressed_fp, mode="wb") as gz:
            shutil.copyfileobj(f, gz)

        conn.put_object(
            Body=compressed_fp.getvalue(),
            Bucket="wort-sra",
            Key=key_path,
            ContentType="application/json",
            ContentEncoding="gzip",
        )


@celery.task
def compute_genomes(accession, path, name):
    import boto3
    import botocore
    from snakemake import shell

    conn = boto3.client("s3")
    s3 = boto3.resource("s3")

    key_path = os.path.join("sigs", accession + ".sig")
    try:
        s3.Object("wort-genomes", key_path).load()
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
            shell(
               f"sourmash compute -k 21,31,51 "
                "  --scaled 1000 "
                "  --track-abundance "
                "  --name {name:q} "
                "  -o {f.name} "
                "  <(curl {path})"
            )
        except CalledProcessError as e:
            # We ignore SIGPIPE, since it is informational (and makes sense,
            # it happens because `head` is closed and `fastq-dump` can't pipe
            # its output anymore. More details:
            # http://www.pixelbeat.org/programming/sigpipe_handling.html
            if e.returncode != 141:
                raise e

        f.seek(0)

        compressed_fp = BytesIO()
        with gzip.GzipFile(fileobj=compressed_fp, mode="wb") as gz:
            shutil.copyfileobj(f, gz)

        conn.put_object(
            Body=compressed_fp.getvalue(),
            Bucket="wort-genomes",
            Key=key_path,
            ContentType="application/json",
            ContentEncoding="gzip",
        )
