#!/usr/bin/env python
"""
Import large JSON.gz TVDB movies data into Django movies models.
Usage: python import_movies.py /path/to/tvdb_movies.jsonl.gz
"""
import gzip
import json
import sys
import os
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import transaction
from movies.models import Movies, MovieGenre, RemoteId, Character, TagOption
from series.models import Genre, Person

BATCH_SIZE = 500  # smaller batches -> more frequent progress updates + smaller failure blast-radius
STATE_FILE = '.import_movies_state'


def save_state(last_tvdb_id):
    with open(STATE_FILE, 'w') as f:
        f.write(str(last_tvdb_id))


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return int(f.read().strip())
    return None


def should_skip(tvdb_id, last_imported_id):
    # Only valid because the source file is crawled/written in ascending tvdb_id order.
    return last_imported_id is not None and tvdb_id <= last_imported_id


def import_file(gz_path):
    print(f"Importing {gz_path}...")

    last_imported_id = load_state()
    if last_imported_id:
        print(f"Resuming after tvdb_id: {last_imported_id}")

    print("Counting total movies...")
    total_lines = sum(1 for line in gzip.open(gz_path, 'rt', encoding='utf-8') if line.strip())
    print(f"Found {total_lines} lines to scan")

    with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
        movies_batch = []
        processed = 0

        pbar = tqdm(total=total_lines, unit='movie', dynamic_ncols=True)
        # NOTE: no upfront pbar.update(last_imported_id) here — that double-counted
        # against the per-line pbar.update(1) calls below and used tvdb_id (an
        # external id) as if it were a line count, which it isn't.

        for line in f:
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)
            if 'tvdb_id' not in obj:
                pbar.update(1)
                continue

            tvdb_id = obj['tvdb_id']
            if should_skip(tvdb_id, last_imported_id):
                pbar.update(1)
                continue

            movies_batch.append(obj)

            if len(movies_batch) >= BATCH_SIZE:
                try:
                    process_batch(movies_batch)
                    processed += len(movies_batch)
                    last_tvdb_id = movies_batch[-1]['tvdb_id']
                    save_state(last_tvdb_id)
                    pbar.update(len(movies_batch))
                    movies_batch.clear()
                except Exception as e:
                    pbar.close()
                    print(f"\nError processing batch: {str(e)}")
                    print(f"Last successful movie: {last_imported_id}")
                    print("You can resume the import by running this script again")
                    sys.exit(1)
            else:
                pbar.update(1)

        if movies_batch:
            try:
                process_batch(movies_batch)
                processed += len(movies_batch)
                last_tvdb_id = movies_batch[-1]['tvdb_id']
                save_state(last_tvdb_id)
            except Exception as e:
                pbar.close()
                print(f"\nError processing final batch: {str(e)}")
                print(f"Last successful movie: {last_imported_id}")
                print("You can resume the import by running this script again")
                sys.exit(1)

        pbar.close()

    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    print(f"Done! Imported {processed} movies.")


def _s(obj, key, default='', maxlen=None):
    """Safe string getter: handles missing key AND explicit null, then truncates."""
    val = obj.get(key, default)
    if val is None:
        val = default
    val = str(val)
    return val[:maxlen] if maxlen else val


def process_batch(batch):
    movies_to_create = []
    raw_by_tvdb_id = {}

    for obj in batch:
        tvdb_id = obj.get('tvdb_id')
        if not tvdb_id:
            continue

        movie = Movies(
            tvdb_id=tvdb_id,
            schema_version=obj.get('schema_version', 1),
            name=_s(obj, 'name', maxlen=500),
            slug=_s(obj, 'slug', maxlen=500),
            image=_s(obj, 'image', maxlen=1000),
            year=_s(obj, 'year', maxlen=10),
            overview=_s(obj, 'overview'),
            original_country=_s(obj, 'original_country', maxlen=100),
            original_language=_s(obj, 'original_language', maxlen=50),
            status=_s(obj, 'status', maxlen=50),
            rate=obj.get('rate'),
            name_en=_s(obj, 'name_en', maxlen=500),
            overview_en=_s(obj, 'overview_en'),
            name_fa=_s(obj, 'name_fa', maxlen=500) if obj.get('name_fa') else None,
        )
        movies_to_create.append(movie)
        raw_by_tvdb_id[tvdb_id] = obj

    # --- Bulk-prefetch genres and persons referenced in this batch to avoid N+1 queries ---
    genre_keys = {}   # tvdb_id -> (name, slug)
    person_keys = {}  # tvdb_id -> (name, image)

    for obj in raw_by_tvdb_id.values():
        for g in obj.get('genres', []):
            gid = g.get('tvdb_id', 0)
            if gid:
                genre_keys[gid] = (g.get('name', ''), g.get('slug', ''))
        for c in obj.get('characters', []):
            pid = c.get('person_tvdb_id', 0)
            if pid:
                person_keys[pid] = ((c.get('person_name', '') or '')[:300], (c.get('person_image', '') or '')[:1000])

    existing_genres = {g.tvdb_id: g for g in Genre.objects.filter(tvdb_id__in=genre_keys.keys())}
    missing_genres = [Genre(tvdb_id=gid, name=name, slug=slug)
                      for gid, (name, slug) in genre_keys.items() if gid not in existing_genres]
    if missing_genres:
        Genre.objects.bulk_create(missing_genres, ignore_conflicts=True)
    genre_map = {g.tvdb_id: g for g in Genre.objects.filter(tvdb_id__in=genre_keys.keys())}

    existing_persons = {p.tvdb_id: p for p in Person.objects.filter(tvdb_id__in=person_keys.keys())}
    missing_persons = [Person(tvdb_id=pid, name=name, image=image)
                       for pid, (name, image) in person_keys.items() if pid not in existing_persons]
    if missing_persons:
        Person.objects.bulk_create(missing_persons, ignore_conflicts=True)
    person_map = {p.tvdb_id: p for p in Person.objects.filter(tvdb_id__in=person_keys.keys())}

    with transaction.atomic():
        Movies.objects.bulk_create(movies_to_create, ignore_conflicts=True)

        saved_movies = Movies.objects.filter(tvdb_id__in=raw_by_tvdb_id.keys())
        movies_map = {m.tvdb_id: m for m in saved_movies}

        genre_links = []
        remote_ids = []
        characters = []

        for tvdb_id, obj in raw_by_tvdb_id.items():
            movie = movies_map.get(tvdb_id)
            if not movie:
                continue

            for g in obj.get('genres', []):
                gid = g.get('tvdb_id', 0)
                genre = genre_map.get(gid)
                if genre is None:
                    # No usable tvdb_id for this genre — skip rather than merging
                    # unrelated genres/persons under a shared id=0 record.
                    continue
                genre_links.append(MovieGenre(movies=movie, genre=genre))

            for rid in obj.get('remote_ids', []):
                remote_ids.append(RemoteId(
                    movies=movie,
                    remote_id=_s(rid, 'remote_id', maxlen=200),
                    id_type=rid.get('id_type', 0),
                    source_name=_s(rid, 'source_name', maxlen=100),
                ))

            for c in obj.get('characters', []):
                pid = c.get('person_tvdb_id', 0)
                person = person_map.get(pid)
                if person is None:
                    continue
                characters.append(Character(
                    tvdb_id=c.get('tvdb_id', 0),
                    movies=movie,
                    person=person,
                    character_name=_s(c, 'character_name', maxlen=300),
                    character_image=_s(c, 'character_image', maxlen=1000),
                    people_type=_s(c, 'people_type', default='Actor', maxlen=50),
                ))

        MovieGenre.objects.bulk_create(genre_links, ignore_conflicts=True)
        RemoteId.objects.bulk_create(remote_ids, ignore_conflicts=True)
        Character.objects.bulk_create(characters, ignore_conflicts=True)


if __name__ == '__main__':
    gz_path = sys.argv[1] if len(sys.argv) > 1 else 'tvdb_movies.jsonl.gz'
    if not os.path.exists(gz_path):
        print(f"File not found: {gz_path}")
        sys.exit(1)
    import_file(gz_path)