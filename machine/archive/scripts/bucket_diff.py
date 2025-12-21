# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "polars",
#     "rich",
#     "s3fs",
#     "sourmash",
# ]
# ///

import asyncio
import io
import hashlib
from datetime import datetime
from itertools import chain, batched
from multiprocessing import Value

import s3fs
import polars as pl
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from sourmash.manifest import BaseCollectionManifest
from sourmash import load_signatures


TEST_DATASETS = [
    "sigs/GCA_000001635.1.sig",
    "sigs/GCA_000001635.2.sig",
    "sigs/GCA_000001635.3.sig",
    "sigs/GCA_000002325.1.sig",
    "sigs/GCA_000003025.2.sig",
]

ARCHIVE_URL = "https://s3.bi.denbi.de"
DATABASES = ["full", "img", "genomes", "sra"]


async def download_original(client, location):
    data = io.BytesIO()
    try:
        f = await client.open_async(location)
        h = hashlib.new("sha256")
        while (chnk := await f.read(1024 * 1024)) != b"":
            h.update(chnk)
            data.write(chnk)
        sha256 = h.hexdigest()
        data.flush()
    finally:
        await f.close()

    return (data, sha256)


async def upload_mirror(client, data, location):
    return await client._pipe_file(
        location, data, ContentType="application/json", ContentEncoding="gzip"
    )


def download_current_manifest(args):
    manifest_url = f"{args.archive_url}/wort-{args.db}/SOURMASH-MANIFEST.parquet"
    manifest_df = pl.scan_parquet(manifest_url)
    return manifest_df


def extract_record(sigs, location, sha256, creation_date, size):
    records = []
    for sig in sigs:
        record = BaseCollectionManifest.make_manifest_row(
            sig, location, include_signature=False
        )
        record["sha256"] = sha256
        record["creation_date"] = datetime.fromisoformat(creation_date)
        record["size"] = size
        record["with_abundance"] = int(record["with_abundance"])
        records.append(record)
    return records


async def main(original_listing, current_manifest, db):
    original = pl.scan_ndjson(original_listing).with_columns(
        pl.col.key.str.strip_prefix(f"s3://wort-{db}/").name.keep()
    )

    unique_locations = current_manifest.unique(subset=["internal_location"]).select([
        "internal_location",
        "size",
    ])

    diff = original.join(
        unique_locations, left_on="key", right_on="internal_location", how="anti"
    )

    download_fs = s3fs.S3FileSystem(
        anon=False,
        profile="default",
    )

    upload_fs = s3fs.S3FileSystem(
        anon=False,
        endpoint_url=ARCHIVE_URL,
        profile="denbi",
    )

    manifest_records = {}
    task_lock = asyncio.Lock()

    download_session = await download_fs.set_session()
    upload_session = await upload_fs.set_session()

    total_tasks = diff.select(pl.len()).collect().item()
    total_bytes = diff.select("size").sum().collect().item()

    current_tasks = Value("i", 0)
    with Progress(
        TextColumn("{task.description}", justify="left"),
        BarColumn(bar_width=None),
        TextColumn(
            "[bold green]{task.fields[task_count].value} / [bold_blue]{task.fields[task_total]}",
            justify="right",
        ),
        "•",
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    ) as progress:
        task_bytes = progress.add_task(
            "[green]Downloading",
            total=total_bytes,
            task_count=current_tasks,
            task_total=total_tasks,
        )
        try:
            for chnk in batched(
                # diff.filter(pl.col.key.is_in(TEST_DATASETS)).collect().iter_rows()
                diff.collect().iter_rows(),
                n=100,
            ):
                tasks = {}
                async with asyncio.TaskGroup() as tg:
                    for key, etag, last_modified, type, size, storage_class in chnk:
                        task = tg.create_task(
                            process_sig(
                                db,
                                key,
                                upload_fs,
                                download_fs,
                                etag,
                                size,
                                last_modified,
                                current_tasks,
                                progress,
                                task_bytes,
                            )
                        )
                        async with task_lock:
                            tasks[key] = task

                for key, task in tasks.items():
                    records = task.result()
                    manifest_records[key] = records
        except* Exception as eg:
            print(*[str(e)[:80] for e in eg.exceptions])
            print(len(eg.exceptions))
        finally:
            await download_session.close()
            await upload_session.close()

    # merge new manifest_records into current_manifest
    # note: will have three records per location!
    new_rows = list(chain.from_iterable(manifest_records.values()))
    new_records = pl.DataFrame(
        new_rows, schema=current_manifest.collect_schema()
    ).lazy()
    new_manifest = pl.concat([current_manifest, new_records])

    # TODO: put new manifest in mirror
    new_manifest.sink_parquet(
        "new_manifest.parquet",
        compression_level=22,
    )

    return new_manifest, diff


async def process_sig(
    db,
    key,
    upload_fs,
    download_fs,
    etag,
    size,
    last_modified,
    current_tasks,
    progress,
    task_bytes,
):
    s3_path = f"s3://wort-{db}/{key}"

    # before downloading, do a head() in mirror
    # and check if etag/size match
    # with this we can avoid re-uploading
    try:
        mirror_info = await upload_fs._info(s3_path)
    except FileNotFoundError:
        uploaded = False
    else:
        uploaded = mirror_info["ETag"] == etag and mirror_info["size"] == size

    # if data is already in mirror, let's download from it instead
    src_fs = download_fs
    if uploaded:
        src_fs = upload_fs

    (data, sha256) = await download_original(src_fs, s3_path)

    raw_sig = data.getvalue()
    sig = load_signatures(raw_sig)

    records = extract_record(sig, key, sha256, last_modified, size)
    if not uploaded:
        _result = await upload_mirror(upload_fs, raw_sig, s3_path)

    with current_tasks.get_lock():
        current_tasks.value += 1
    progress.update(task_bytes, advance=size)

    return records


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a", "--archive-url", default=ARCHIVE_URL, help="Base URL for the main archive"
    )
    parser.add_argument(
        "--db",
        default="img",
        choices=DATABASES,
        metavar="database",
        help=f"Which database to download. Available databases: {', '.join(DATABASES)}",
    )
    parser.add_argument("original_listing")
    # parser.add_argument("mirror_listing")
    # parser.add_argument("current_manifest")

    args = parser.parse_args()

    current_manifest = download_current_manifest(args)

    new_manifest, diff = asyncio.run(
        main(args.original_listing, current_manifest, args.db)
    )

    print(diff.head(5).collect())
    print(diff.count().collect())

    print(new_manifest.tail(5).collect())
    print(new_manifest.count().collect())
