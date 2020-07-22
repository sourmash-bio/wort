from glob import glob

n = 0
for hashes in reversed(glob("machine/wort-web/hashes/wort_hashes*")):
    with open(hashes, 'r') as fp:
        for line in fp:
            try:
                _, ipfs, key = line.strip().split()
            except:
                continue

            if key.startswith("wort-sra"):
                public_db = "sra"
                key = key[14:-4]
            elif key.startswith("wort-img"):
                public_db = "img"
                key = key[14:-4]
            elif key.startswith("GC"):
                # These are wort-genomes sigs
                public_db = "genomes"
                key = key[:-4]
            elif not key.startswith("wort-"):
                # These are generated for wort-sra
                #key = f"wort-sra/sigs/{key}"
                public_db = "sra"
                key = key[:-4]
            else:
                # not sure what to do with this one...
                continue

            dataset = Dataset.query.filter_by(id=key).first()
            if dataset is None:
                if public_db == "sra":
                    # if it's SRA, don't add it (run add_dataset_info.py first)
                    continue
                elif public_db == "img":
                    # we don't have extra metadata for IMG (yet), so add new dataset
                    dataset = Dataset(id=key, database_id="IMG", size_MB=None, ipfs=ipfs)
                    db.session.add(dataset)
                    n += 1
                    app.cache.delete(f"{public_db}/{key}")
                    # TODO: set cache key? Might just leave it to 'view' and avoid duplicating logic
            else:
                # Dataset already added, check if ipfs is set
                if dataset.ipfs is None:
                    dataset.ipfs = ipfs
                    db.session.add(dataset)
                    n += 1
                    app.cache.delete(f"{public_db}/{key}")
                    # TODO: maybe update cache here

            if (n % 1000 == 0) and (n != 0):
                # Avoid committing all at once or one by one?
                n = 0
                db.session.commit()
