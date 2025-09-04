# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "polars",
# ]
# ///

import polars as pl


def main(args):
    manifest_df = pl.scan_csv(args.manifest, skip_rows=1)
    sha256_df = pl.scan_csv(
        args.sha256,
        has_header=False,
        separator=" ",
        new_columns=["sha256", "sep", "path"],
    ).drop("sep")
    df = manifest_df.join(sha256_df, left_on="internal_location", right_on="path")
    if args.basepath:
        df = df.with_columns(
            pl.col("internal_location").str.strip_prefix(args.basepath)
        )

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

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--basepath", default=None)
    parser.add_argument("-F", "--format", choices=["parquet", "csv"], default="parquet")
    parser.add_argument("manifest")
    parser.add_argument("sha256")
    parser.add_argument("output", type=argparse.FileType("w", encoding="utf-8"))

    args = parser.parse_args()

    main(args)
