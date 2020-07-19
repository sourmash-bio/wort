import csv
import sys

n = 0
with open(sys.argv[1], 'r') as fp:
    datasets = csv.DictReader(fp, delimiter=',')
    for row in datasets:
        dataset_in_db = Dataset.query.filter_by(id=row['Run']).first()

        # if dataset_in_db doesn't exist, create a new one
        if dataset_in_db is None:
            new_dataset = Dataset(id=row["Run"], database_id="SRA", size_MB=row["size_MB"], ipfs=None)
            db.session.add(new_dataset)
            n += 1
        else:
            # TODO: dataset is in DB, do we want to update it?
            # If it was updated, invalidate cache
            pass

        if n % 1000 == 0:
            # Avoid committing all at once?
            n = 0
            db.session.commit()

    db.session.commit()
