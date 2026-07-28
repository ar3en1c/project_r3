import argparse
import csv
import gzip
import os
import time
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.db import transaction

from series.models import RemoteId, Series


def import_ratings(
    ratings_path,
    source_name,
    batch_size,
    dry_run,
    progress_every,
):
    totals = {"rows": 0, "matched": 0, "updated": 0}
    ratings = {}
    started_at = time.monotonic()

    print(f"Reading {ratings_path}...")
    with gzip.open(ratings_path, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")

        if not reader.fieldnames or not {"tconst", "averageRating"}.issubset(
            reader.fieldnames
        ):
            raise ValueError("Expected IMDb columns: tconst and averageRating")

        for row in reader:
            totals["rows"] += 1

            try:
                ratings[row["tconst"]] = float(row["averageRating"])
            except (KeyError, TypeError, ValueError):
                continue

            if len(ratings) >= batch_size:
                update_batch(ratings, source_name, batch_size, dry_run, totals)
                ratings.clear()

            if totals["rows"] % progress_every == 0:
                show_progress(totals, started_at, dry_run)

    if ratings:
        update_batch(ratings, source_name, batch_size, dry_run, totals)

    action = "Would update" if dry_run else "Updated"
    show_progress(totals, started_at, dry_run, final=True)
    print(
        f"{action} {totals['updated']} series from {totals['rows']} IMDb rows "
        f"({totals['matched']} matching IDs)."
    )


def show_progress(totals, started_at, dry_run, final=False):
    elapsed = time.monotonic() - started_at
    rows_per_second = totals["rows"] / elapsed if elapsed else 0
    message = (
        f"\rScanned: {totals['rows']:,} rows | "
        f"Matched: {totals['matched']:,} | "
        f"{'Would update' if dry_run else 'Updated'}: "
        f"{totals['updated']:,} | "
        f"Speed: {rows_per_second:,.0f} rows/sec"
    )
    print(message, end="\n" if final else "", flush=True)


def update_batch(ratings, source_name, batch_size, dry_run, totals):
    remote_ids = RemoteId.objects.filter(
        source_name__iexact=source_name,
        remote_id__in=ratings,
    ).select_related("series")

    series_to_update = []

    for remote_id in remote_ids.iterator(chunk_size=batch_size):
        totals["matched"] += 1
        new_rating = ratings[remote_id.remote_id]

        if remote_id.series.rate != new_rating:
            remote_id.series.rate = new_rating
            series_to_update.append(remote_id.series)

    totals["updated"] += len(series_to_update)

    if not dry_run and series_to_update:
        with transaction.atomic():
            Series.objects.bulk_update(
                series_to_update,
                ["rate"],
                batch_size=batch_size,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ratings_file")
    parser.add_argument("--source-name", default="imdb")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50000,
        help="Show progress after this many IMDb rows (default: 50000).",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ratings_path = Path(args.ratings_file)
    if not ratings_path.is_file():
        parser.error(f"File not found: {ratings_path}")
    if args.batch_size < 1:
        parser.error("--batch-size must be greater than zero")
    if args.progress_every < 1:
        parser.error("--progress-every must be greater than zero")

    import_ratings(
        ratings_path,
        args.source_name,
        args.batch_size,
        args.dry_run,
        args.progress_every,
    )
