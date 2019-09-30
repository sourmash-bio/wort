import gzip
from io import BytesIO
import os
from subprocess import CalledProcessError
import shutil
from tempfile import NamedTemporaryFile

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
            self._index = SBT.load('genbank', leaf_loader=SigLeaf.load)
        return self._index


@celery.task(base=SearchGenbank)
def search_genbank(signature):
    sbt = [(search_genbank.index, 'genbank', True)]
    threshold = 0.9
    containment = False
    best_only = False
    ignore_abundance = False

    query = load_sig(signature)

    results = search_databases(query, sbt,
                               threshold, containment,
                               best_only, ignore_abundance)
