from base64 import b64decode
import gzip
from io import BytesIO
import os
from subprocess import CalledProcessError
import shutil
from tempfile import NamedTemporaryFile

from sourmash import load_one_signature
from sourmash.sbt import SBT
from sourmash.sbtmh import SigLeaf
from sourmash.search import search_databases

from wort.app import create_celery_app

celery = create_celery_app()


class SearchGenbank(celery.Task):
    _index = None

    @property
    def index(self):
        if self._index is None:
            self._index = SBT.load(str(celery.conf.WORT_DATABASES_PATH.joinpath("genbank-d2-k21")), leaf_loader=SigLeaf.load)
        return self._index


@celery.task(base=SearchGenbank)
def search_genbank(signature):
    index = [(search_genbank.index, 'genbank', 'SBT')]
    threshold = 0.99
    containment = False
    best_only = True
    ignore_abundance = False

    sig = b64decode(signature).decode("ascii")

    query = load_one_signature(sig, ksize=21)
    print(query)

    results = search_databases(query, index,
                               threshold, containment,
                               best_only, ignore_abundance)

    print(results)
    return results
