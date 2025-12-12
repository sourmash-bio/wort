# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "polars",
# ]
# ///

import polars as pl


def main(args):
    df = pl.read_ndjson(args.update_log).select(['source'])

    print(df.head(5))

    for row in df.iter_rows():
        args.cmds.write(f"ls {row[0]}\n")


if __name__ == "__main__":
    import argparse
    import pathlib

    parser = argparse.ArgumentParser()
    parser.add_argument("update_log", type=pathlib.Path)
    parser.add_argument("cmds", type=argparse.FileType("w", encoding="utf-8"))

    args = parser.parse_args()

    main(args)
