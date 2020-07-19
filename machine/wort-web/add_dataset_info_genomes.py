import csv
import gzip
import sys

import requests


def build_link(accession, asm_name):
    db, acc = accession.split("_")
    number, version = acc.split(".")
    number = "/".join([number[pos:pos + 3] for pos in range(0, len(number), 3)])
    url = f"ftp://ftp.ncbi.nlm.nih.gov/genomes/all/{db}/{number}"
    return f"{url}/{accession}_{asm_name}"


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
                if row['ftp_path'] == "na":
                    # check if 'gbrs_paired_asm' is available and
                    # 'paired_asm_comp' is 'identical'
                    if row['paired_asm_comp'] == 'identical':
                        row['ftp_path'] = build_link(row['gbrs_paired_asm'], row['asm_name'])
                    else: # need to rebuild path from this accession...
                        row['ftp_path'] = build_link(row['assembly_accession'], row['asm_name'])
                http_path = 'https' + row['ftp_path'][3:]
                filename = http_path.split('/')[-1]
                path = f"{http_path}/{filename}_genomic.fna.gz"

                name_parts = [row["assembly_accession"], " ", row['organism_name']]
                if row['infraspecific_name']:
                    name_parts += [" ", row['infraspecific_name']]
                name_parts += [', ', row['asm_name']]
                name = "".join(name_parts)[:128]

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
                # TODO: dataset is in DB, do we want to update it?
                # If it was updated, invalidate cache
                pass

            if (n % 100 == 0) and (n != 0):
                # Avoid committing all at once?
                total += n
                #print(f"Processed {total} datasets")
                n = 0
                db.session.commit()

        db.session.commit()
