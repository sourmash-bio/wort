import csv
import os
import sys

import boto3
import botocore

conn = boto3.client("s3")
s3 = boto3.resource("s3")


n = 0
with open(sys.argv[1], 'r') as fp:
    datasets = csv.DictReader(fp, delimiter=',')
    for row in datasets:
        if row["size_MB"] == "size_MB":
            # dumb error from entrez-direct, it repeats the header in the middle =/
            continue

        dataset_in_db = Dataset.query.filter_by(id=row['Run']).first()
        sra_id = row["Run"]

        # if dataset_in_db doesn't exist, create a new one
        if dataset_in_db is None:
            new_dataset = Dataset(id=sra_id, database_id="SRA", size_MB=row["size_MB"], ipfs=None)
            db.session.add(new_dataset)
            n += 1
        else:
            updated = False
            # dataset is in DB, do we want to update it?
            if dataset_in_db.computed is None:
                # check on S3
                key_path = os.path.join("sigs", sra_id + ".sig")
                try:
                    obj = s3.Object("wort-sra", key_path)
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
                app.cache.delete(f"sra/{sra_id}")

        if n % 1000 == 0:
            # Avoid committing all at once?
            n = 0
            db.session.commit()

    db.session.commit()
