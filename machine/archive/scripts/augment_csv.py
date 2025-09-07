# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "polars",
# ]
# ///

from datetime import datetime

import polars as pl


def main(args):
    manifest_df = pl.scan_csv(args.manifest, skip_rows=1)
    sha256_df = pl.scan_csv(
        args.sha256,
        has_header=False,
        separator=" ",
        new_columns=["sha256", "sep", "path"],
    ).drop("sep")

    s3_metadata = {
        "creation_date": [],
        "size": [],
        "filename": [],
    }
    with args.s3_metadata.open() as f:
        for line in f:
            try:
                date, time, size, filename = line.strip().split()
            except:
                print(f"skipping line {line}")
                continue

            dt = datetime(
                *[int(v) for v in date.split("/")], *[int(v) for v in time.split(":")]
            )
            s3_metadata["creation_date"].append(dt)
            s3_metadata["size"].append(int(size))
            s3_metadata["filename"].append(f"sigs/{filename}")

    s3_metadata_df = pl.from_dict(
        s3_metadata,
        schema={
            "creation_date": pl.Datetime,
            "size": pl.Int64,
            "filename": pl.String,
        },
    ).lazy()

    print(s3_metadata_df.head(5).collect())

    df = manifest_df.join(sha256_df, left_on="internal_location", right_on="path")
    if args.basepath:
        df = df.with_columns(
            pl.col("internal_location").str.strip_prefix(args.basepath)
        )

    print(f"after join sha256:\n{df.head(5).collect()}")

    df = df.join(s3_metadata_df, left_on="internal_location", right_on="filename")

    print(f"after join S3:\n{df.head(5).collect()}")

    match args.format:
        case "parquet":
            df.sink_parquet(
                args.output,
                compression_level=22,
                metadata={"SOURMASH-MANIFEST-VERSION": "1.0"},
            )
        case "csv":
            args.output.writelines(["# SOURMASH-MANIFEST-VERSION: 1.0\n"])
            df.sink_csv(args.output)
        case _:
            print("Unknown output format")


if __name__ == "__main__":
    import argparse
    import pathlib

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--basepath", default=None)
    parser.add_argument("-F", "--format", choices=["parquet", "csv"], default="parquet")
    parser.add_argument("manifest")
    parser.add_argument("sha256")
    parser.add_argument("s3_metadata", type=pathlib.Path)
    parser.add_argument("output", type=argparse.FileType("w", encoding="utf-8"))

    args = parser.parse_args()

    main(args)
