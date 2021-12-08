import csv
import gzip
import os
import sys

import boto3
import botocore
import requests

conn = boto3.client("s3")
s3 = boto3.resource("s3")


def build_link(accession, asm_name):
    db, acc = accession.split("_")
    number, version = acc.split(".")
    number = "/".join([number[pos:pos + 3] for pos in range(0, len(number), 3)])
    url = f"https://ftp.ncbi.nlm.nih.gov/genomes/all/{db}/{number}"
    return f"{url}/{accession}_{asm_name}"


def crawl_link(accession, session):
    db, acc = accession.split("_")
    number, version = acc.split(".")
    number = "/".join([number[pos:pos + 3] for pos in range(0, len(number), 3)])
    url = f"https://ftp.ncbi.nlm.nih.gov/genomes/all/{db}/{number}"

    asm_name = None
    req = session.get(url)
    if req.status_code == 200:
        # try to read the right accession name
        for line in req.text.split('\n'):
            if line.startswith(f'<a href="{accession}_'):
                asm_name = line.split('"')[1][:-1]
                break
    # TODO: check for 5xx

    if asm_name is None:
        raise ValueError(f"Couldn't find link for {accession}")

    return f"{url}/{asm_name}/{asm_name}_genomic.fna.gz"


n = 0
total = 0
with requests.Session() as s:
    with gzip.open(sys.argv[1], 'rt') as fp:
        fp.readline() # Skip first line
        fp.read(2) # skip initial comment in header

        datasets = csv.DictReader(fp, delimiter='\t')
        for row in datasets:
            dataset_in_db = Dataset.query.filter_by(id=row['assembly_accession']).first()

            # if dataset_in_db doesn't exist, create a new one
            if dataset_in_db is None:
                # Build the signature name
                name_parts = [row["assembly_accession"], " ", row['organism_name']]
                if row['infraspecific_name']:
                    name_parts += [" ", row['infraspecific_name']]
                name_parts += [', ', row['asm_name']]
                name = "".join(name_parts)[:128]

                # Let's find the right download path
                if row['ftp_path'] == "na":
                    # check if 'gbrs_paired_asm' is available and
                    # 'paired_asm_comp' is 'identical'
                    if row['paired_asm_comp'] == 'identical':
                        row['ftp_path'] = build_link(row['gbrs_paired_asm'], row['asm_name'])
                    else: # need to rebuild path from this accession...
                        row['ftp_path'] = build_link(row['assembly_accession'], row['asm_name'])

                # 2021-11-22: ftp_path points to https now
                http_path = row['ftp_path']
                filename = http_path.split('/')[-1]
                path = f"{http_path}/{filename}_genomic.fna.gz"

                # Let's check if the path exists
                check_r = s.head(path)
                if check_r.status_code == 404:
                    # Error with this path, let's try to crawl instead
                    try:
                        path = crawl_link(row['assembly_accession'], s)
                    except ValueError:
                        # Can't find this data, continue...
                        continue
                elif check_r.status_code >= 500:
                    # Server error, try again
                    os.sleep(2)
                    check_r = s.head(path)
                    if check_r.status_code >= 500:
                        # ¯\_(ツ)_/¯ let's retry it some other time...
                        continue

                # Assembly summary doesn't include size of dataset
                # Let's use a cheap head request to find the size
                size_r = s.head(path)
                if size_r.status_code == 404:
                    print(f"Error 404 on {path}")
                    continue
                size_MB = int(int(size_r.headers['Content-Length']) / 1000000)

                new_dataset = Dataset(
                    id=row["assembly_accession"],
                    database_id="Genomes",
                    size_MB=size_MB,
                    ipfs=None,
                    path=path,
                    name=name
                )
                db.session.add(new_dataset)
                n += 1
            else:
                updated = False
                # dataset is in DB, do we want to update it?
                if dataset_in_db.computed is None:
                    acc = row["assembly_accession"]
                    # check on S3
                    key_path = os.path.join("sigs", acc + ".sig")
                    try:
                        obj = s3.Object("wort-genomes", key_path)
                        obj.load()
                    except botocore.exceptions.ClientError as e:
                        if e.response["Error"]["Code"] == "404":
                            pass  # Object does not exist yet
                        else:
                            # Something else has gone wrong
                            raise
                    else:
                        # The key already exists, update compute field in DB
                        dataset_in_db.computed = obj.last_modified
                        db.session.add(dataset_in_db)
                        updated = True

                # If it was updated, invalidate cache
                if updated:
                    print(f"Updating {acc}")
                    app.cache.delete(f"genomes/{acc}")

            if (n % 100 == 0) and (n != 0):
                # Avoid committing all at once?
                total += n
                print(f"Processed {total} datasets")
                n = 0
                db.session.commit()

        db.session.commit()
