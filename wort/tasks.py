import os
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile, TemporaryDirectory

from celery.exceptions import Ignore

from .app import app


@app.task
def compute(sra_id):
    from snakemake import shell
    with TemporaryDirectory() as tmpdir:
        with NamedTemporaryFile('w+t') as f:
            try:
                shell('fastq-dump -A {sra_id} -Z | '
                    'head -4000000 | '
                    'trim-low-abund.py -T {tmpdir} -M 5e8 -k 21 -V -Z 10 -C 3 - -o - | '
                    'sourmash compute -f -k 21 --dna - -o {output} --name {sra_id}'
                    .format(sra_id=sra_id,
                            output=f.name,
                            tmpdir=tmpdir))
            except CalledProcessError as e:
                # We ignore SIGPIPE, since it is informational (and makes sense,
                # it happens because `head` is closed and `fastq-dump` can't pipe
                # its output anymore. More details:
                # http://www.pixelbeat.org/programming/sigpipe_handling.html
                if e.returncode != 141:
                    raise e

            f.seek(0)
            return f.read()


@app.task
def compute_syrah(sra_id):
    from snakemake import shell
    with NamedTemporaryFile('w+t') as f:
        try:
            shell('fastq-dump -A {sra_id} -Z | syrah | '
                  'sourmash compute -k 21 --dna - -o {output} --name {sra_id}'
                  .format(sra_id=sra_id,
                          output=f.name))
        except CalledProcessError as e:
            # We ignore SIGPIPE, since it is informational (and makes sense,
            # it happens because `head` is closed and `fastq-dump` can't pipe
            # its output anymore. More details:
            # http://www.pixelbeat.org/programming/sigpipe_handling.html
            if e.returncode != 141:
                raise e

        f.seek(0)
        return f.read()


@app.task(bind=True, ignore_result=True)
def compute_syrah_to_s3(self, sra_id):
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    from snakemake import shell

    conn = S3Connection()
    bucket = conn.get_bucket("soursigs-done")

    # Check if file is already on S3
    key = bucket.get_key(os.path.join('sigs', sra_id))
    if key is None:  # result not available yet, compute it
        with NamedTemporaryFile('w+t') as f:
            try:
                shell('fastq-dump -A {sra_id} -Z | syrah | '
                      'sourmash compute -k 21 --dna - -o {output} --name {sra_id}'
                      .format(sra_id=sra_id,
                              output=f.name))
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
            k.key = os.path.join('sigs', sra_id)
            f.seek(0)
            k.set_contents_from_string(f.read())

            raise Ignore()
