# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "aiofiles",
#     "httpx",
#     "httpx-retries",
#     "polars",
# ]
# ///

import hashlib
import shutil

import aiofiles
import httpx
import polars as pl
from httpx_retries import RetryTransport


ARCHIVE_URL = "https://farm.cse.ucdavis.edu/~irber"
DATABASES = ["full", "img", "genomes", "sra"]


async def main(args):
    manifest_url = f"{args.archive_url}/wort-{args.database}/SOURMASH-MANIFEST.parquet"
    manifest_df = (
        pl.scan_parquet(manifest_url)
        .select(["internal_location", "sha256"])
        .unique(subset=["internal_location"])
    )

    limiter = asyncio.Semaphore(args.max_downloaders)

    already_mirrored_locations = set()
    async with limiter:
        for root, dirs, files in args.basedir.walk(top_down=True):
            for name in files:
                already_mirrored_locations.add(
                    str(root.relative_to(args.basedir) / name)
                )
    print(len(already_mirrored_locations))

    if args.full_check:
        # check sha56
        internal_locations = []
        sha256_sums = []

        for location in already_mirrored_locations:
            async with aiofiles.open(args.basedir / location, mode="rb") as f:
                h = hashlib.new("sha256")
                while (chnk := await f.read(1024 * 1024)) != b"":
                    h.update(chnk)
                sha256 = h.hexdigest()

                internal_locations.append(location)
                sha256_sums.append(sha256)
    else:
        internal_locations = list(already_mirrored_locations)

    print(f"{len(internal_locations)} sha256 calculated")

    already_mirrored = {"internal_location": internal_locations}
    join_columns = ["internal_location"]
    schema = {"internal_location": pl.String}

    if args.full_check:
        already_mirrored["sha256"] = sha256_sums
        schema["sha256"] = pl.String
        join_columns.append("sha256")

    already_mirrored_df = pl.from_dict(already_mirrored, schema=schema).lazy()
    print(already_mirrored_df.collect())

    to_mirror_df = manifest_df.join(already_mirrored_df, on=join_columns, how="anti")

    print(to_mirror_df.collect())

    (args.basedir / "sigs").mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(
        timeout=30.0,
        # limits=httpx.Limits(max_connections=args.max_downloaders),
        base_url=f"{args.archive_url}/wort-{args.database}/",
        transport=RetryTransport(),
    ) as client:
        try:
            async with asyncio.TaskGroup() as tg:
                for location, sha256 in to_mirror_df.collect().iter_rows():
                    tg.create_task(
                        download_sig(
                            location,
                            sha256,
                            args.basedir,
                            client,
                            limiter,
                            args.dry_run,
                        )
                    )
        except* Exception as eg:
            print(*[str(e)[:80] for e in eg.exceptions])
            print(len(eg.exceptions))
        else:
            # copy manifest
            if args.dry_run:
                print(f"download: {manifest_url}")
                return

            async with client.stream("GET", "SOURMASH-MANIFEST.parquet") as response:
                async with aiofiles.tempfile.NamedTemporaryFile() as f:
                    async for chnk in response.aiter_raw(1024 * 1024):
                        await f.write(chnk)
                    await f.flush()

                    await asyncio.to_thread(
                        shutil.copyfile,
                        f.name,
                        args.basedir / "SOURMASH-MANIFEST.parquet",
                    )


async def download_sig(location, sha256, basedir, client, limiter, dry_run):
    async with limiter:
        if dry_run:
            print(f"download: {location}")
            return

        async with client.stream("GET", location) as response:
            h = hashlib.new("sha256")
            total_bytes = 0
            response.raise_for_status()
            # download to temp location
            async with aiofiles.tempfile.NamedTemporaryFile() as f:
                async for chnk in response.aiter_raw(1024 * 1024):
                    h.update(chnk)
                    await f.write(chnk)
                    total_bytes += len(chnk)

                if sha256 != h.hexdigest():
                    # TODO: raise exception, download failed?
                    #       or maybe retry?
                    print(f"download failed! expected {sha256}, got {h.hexdigest()}")

                await f.flush()

                # move to final location
                print(f"completed {location}, {total_bytes:,} bytes")
                await asyncio.to_thread(shutil.copyfile, f.name, basedir / location)


if __name__ == "__main__":
    import argparse
    import asyncio
    import pathlib

    parser = argparse.ArgumentParser(
        description="A tool for mirroring wort data from the main archive"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        default=False,
        action="store_true",
        help="Skip download, useful to check what would be downloaded",
    )
    parser.add_argument(
        "-a", "--archive-url", default=ARCHIVE_URL, help="Base URL for the main archive"
    )
    parser.add_argument(
        "-m",
        "--max-downloaders",
        type=int,
        default=30,
        help="Maximum number of downloads to execute concurrently",
    )
    parser.add_argument(
        "-f",
        "--full-check",
        default=False,
        action="store_true",
        help="Calculate sha256 for local files, instead of depending only on filename",
    )
    parser.add_argument(
        "database",
        default="img",
        choices=DATABASES,
        metavar="database",
        help=f"Which database to download. Available databases: {', '.join(DATABASES)}",
    )
    parser.add_argument(
        "basedir",
        type=pathlib.Path,
        help="base directory for the mirror (existing or new)",
    )

    args = parser.parse_args()

    asyncio.run(main(args))
