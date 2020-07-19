import sys
import time

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError

filename = sys.argv[1]

genomes = pd.read_table(filename, header=1, usecols=["# assembly_accession"])
accessions = genomes["# assembly_accession"]

url  ="https://wort.oxli.org"
# TODO: read PASSWORD from env

token = (requests.post(url + '/v1/auth/tokens',
                      auth=HTTPBasicAuth('luizirber', PASSWORD))
                .text)

for accession in accessions:
    retry = 3
    while retry:
        try:
            r = requests.post(f"{url}/v1/compute/genomes/{accession}",
                    headers={'Authorization': f"Bearer {token}"})
            if r.status_code == 401:
                token = (requests.post(url + '/v1/auth/tokens',
                                      auth=HTTPBasicAuth('luizirber', PASSWORD))
                                .text)
                r = requests.post(f"{url}/v1/compute/genomes/{accession}",
                        headers={'Authorization': f"Bearer {token}"})
            try:
                if 'Signature already calculated' not in r.json():
                    print(accession)
            except:
                pass

            retry = False
        except ConnectionError as e:
            time.sleep(10)
            retry -= 1
