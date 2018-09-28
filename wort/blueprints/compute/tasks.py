import gzip
from io import BytesIO
import os
from subprocess import CalledProcessError
import shutil
from tempfile import NamedTemporaryFile, TemporaryDirectory

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
                "fastq-dump --fasta 0 -A {sra_id} -Z | "
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

        # TODO: compress using gzip here!
        # TODO: need to fix those already in S3 first...
        # compressed_fp = BytesIO()
        # with gzip.GzipFile(fileobj=compressed_fp, mode="wb") as gz:
        #    shutil.copyfileobj(f, gz)

        # conn.put_object(
        #    Body=compressed_fp.getvalue(),
        #    Bucket="wort-sra",
        #    Key=key_path,
        #    ContentType="text/plain",
        #    ContentEncoding="gzip",
        # )

        # save to S3
        key = s3.Object("wort-sra", key_path)
        key.upload_fileobj(f)


@celery.task
def compute_syrah(sra_id):
    from snakemake import shell

    with NamedTemporaryFile("w+t") as f:
        try:
            shell(
                "fastq-dump -A {sra_id} -Z | syrah | "
                "sourmash compute -k 21 --dna - -o {output} --name {sra_id}".format(
                    sra_id=sra_id, output=f.name
                )
            )
        except CalledProcessError as e:
            # We ignore SIGPIPE, since it is informational (and makes sense,
            # it happens because `head` is closed and `fastq-dump` can't pipe
            # its output anymore. More details:
            # http://www.pixelbeat.org/programming/sigpipe_handling.html
            if e.returncode != 141:
                raise e

        f.seek(0)
        return f.read()


@celery.task(bind=True, ignore_result=True)
def compute_syrah_to_s3(self, sra_id):
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    from snakemake import shell

    conn = S3Connection()
    bucket = conn.get_bucket("soursigs-done")

    # Check if file is already on S3
    key = bucket.get_key(os.path.join("sigs", sra_id))
    if key is None:  # result not available yet, compute it
        with NamedTemporaryFile("w+t") as f:
            try:
                shell(
                    "fastq-dump -A {sra_id} -Z | syrah | "
                    "sourmash compute -k 21 --dna - -o {output} --name {sra_id}".format(
                        sra_id=sra_id, output=f.name
                    )
                )
            except CalledProcessError as e:
                # We ignore SIGPIPE, since it is informational (and makes sense,
                # it happens because `head` is closed and `fastq-dump` can't pipe
                # its output anymore. More details:
                # http://www.pixelbeat.org/programming/sigpipe_handling.html
                if e.returncode != 141:
                    # TODO: save error to bucket, on 'errors/{sra_id}'?
                    raise e

            # save to S3
            k = Key(bucket)
            k.key = os.path.join("sigs", sra_id)
            f.seek(0)
            k.set_contents_from_string(f.read())

            raise Ignore()
