#!/usr/bin/env python
"""
Backfill image + overview onto existing Movies rows from tvdb_movie_images.jsonl.gz.

The crawler stores one overview per movie (Persian if available, else English);
it maps to Movies.overview. We only overwrite a field when the file has a
non-empty value for it, so existing rows aren't blanked by partial records.

Usage:
    python scripts/import_movie_images.py [tvdb_movie_images.jsonl.gz] [--dry-run] [--batch-size 5000]
"""
import gzip
import json
import os
import sys
from pathlib import Path

# Ensure the project root is importable when run from anywhere (e.g. `python scripts/x.py`),
# so `config.settings` resolves the same as `manage.py` does.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from tqdm import tqdm

from movies.models import Movies


def load_records(gz_path):
    """tvdb_id -> {image, overview} (only non-empty values kept)."""
    print(f"Reading {gz_path}...")
    records = {}
    with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
        for line in tqdm(f, unit='line', dynamic_ncols=True):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            tvdb_id = obj.get('tvdb_id')
            if not tvdb_id:
                continue
            rec = {}
            if obj.get('image'):
                rec['image'] = str(obj['image'])[:1000]
            if obj.get('overview'):
                rec['overview'] = str(obj['overview'])
            if rec:
                records[tvdb_id] = rec
    print(f"Loaded {len(records):,} records with image/overview.")
    return records


def import_records(records, batch_size, dry_run):
    """Patch existing Movies rows; skipped rows (no match / already current) are counted."""
    tvdb_ids = list(records)
    print(f"Matching {len(tvdb_ids):,} tvdb_ids against existing rows...")

    stats = {'scanned': len(tvdb_ids), 'matched': 0, 'updated': 0}
    to_update = []  # movies with at least one changed field

    qs = Movies.objects.filter(tvdb_id__in=tvdb_ids).only('id', 'tvdb_id', 'image', 'overview')
    for movie in tqdm(qs.iterator(chunk_size=batch_size), total=len(tvdb_ids),
                      unit='match', dynamic_ncols=True):
        stats['matched'] += 1
        rec = records.get(movie.tvdb_id)
        if not rec:
            continue
        changed = False
        if 'image' in rec and movie.image != rec['image']:
            movie.image = rec['image']
            changed = True
        # ponytail: overview update checks both directions — only overwrite when the
        # new value differs, so a row that already has a better/different overview
        # isn't needlessly bumped (updated_at churn via auto_now).
        if 'overview' in rec and movie.overview != rec['overview']:
            movie.overview = rec['overview']
            changed = True
        if changed:
            stats['updated'] += 1
            to_update.append(movie)
            if len(to_update) >= batch_size:
                if not dry_run:
                    Movies.objects.bulk_update(to_update, ['image', 'overview'], batch_size=batch_size)
                to_update.clear()

    if to_update and not dry_run:
        Movies.objects.bulk_update(to_update, ['image', 'overview'], batch_size=batch_size)

    verb = 'Would update' if dry_run else 'Updated'
    print(f"\n{verb} {stats['updated']:,} movies (matched {stats['matched']:,} / "
          f"scanned {stats['scanned']:,}).")
    return stats


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', nargs='?', default='tvdb_movie_images.jsonl.gz',
                        help='Path to tvdb_movie_images.jsonl.gz (default: ./tvdb_movie_images.jsonl.gz)')
    parser.add_argument('--dry-run', action='store_true', help='Show counts without writing.')
    parser.add_argument('--batch-size', type=int, default=5000,
                        help='Chunk size for bulk_update + iterator (default: 5000).')
    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error('--batch-size must be greater than zero')

    gz_path = Path(args.file)
    if not gz_path.is_file():
        print(f"File not found: {gz_path}", file=sys.stderr)
        sys.exit(1)

    records = load_records(gz_path)
    import_records(records, args.batch_size, args.dry_run)
