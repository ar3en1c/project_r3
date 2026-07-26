#!/usr/bin/env python
"""
Import large JSON.gz TVDB movies data into Django movies models.
Usage: python import_movies.py /path/to/tvdb_movies.jsonl.gz
"""
import gzip
import json
import sys
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from movies.models import Movies, MovieGenre, RemoteId, Character, TagOption
from series.models import Genre, Person

BATCH_SIZE = 5000

genre_cache = {}
person_cache = {}

def get_or_create_genre(tvdb_id, name, slug):
    key = (tvdb_id, name)
    if key in genre_cache:
        return genre_cache[key]
    genre, _ = Genre.objects.get_or_create(
        tvdb_id=tvdb_id,
        defaults={'name': name, 'slug': slug}
    )
    genre_cache[key] = genre
    return genre

def get_or_create_person(tvdb_id, name, image):
    key = tvdb_id
    if key in person_cache:
        return person_cache[key]
    person, _ = Person.objects.get_or_create(
        tvdb_id=tvdb_id,
        defaults={'name': name, 'image': image}
    )
    person_cache[key] = person
    return person

def import_file(gz_path):
    print(f"Importing {gz_path}...")

    movies_batch = []
    processed = 0

    with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)
            if 'tvdb_id' not in obj:
                continue

            movies_batch.append(obj)

            if len(movies_batch) >= BATCH_SIZE:
                process_batch(movies_batch)
                processed += len(movies_batch)
                print(f"  Processed {processed} movies...")
                movies_batch.clear()

        if movies_batch:
            process_batch(movies_batch)
            processed += len(movies_batch)
            print(f"  Processed {processed} movies total")

    print(f"Done! Imported {processed} movies.")

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
            name=(obj.get('name', '') or '')[:500],
            slug=(obj.get('slug', '') or '')[:500],
            image=(obj.get('image', '') or '')[:1000],
            year=(obj.get('year', '') or '')[:10],
            overview=obj.get('overview', '') or '',
            original_country=(obj.get('original_country', '') or '')[:100],
            original_language=(obj.get('original_language', '') or '')[:50],
            status=(obj.get('status', '') or '')[:50],
            rate=obj.get('rate'),
            name_en=(obj.get('name_en', '') or '')[:500],
            overview_en=obj.get('overview_en', '') or '',
            name_fa=(obj.get('name_fa', '') or '')[:500] if obj.get('name_fa') else None,
        )
        movies_to_create.append(movie)
        raw_by_tvdb_id[tvdb_id] = obj

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
            genre = get_or_create_genre(
                g.get('tvdb_id', 0),
                g.get('name', ''),
                g.get('slug', '')
            )
            genre_links.append(MovieGenre(movies=movie, genre=genre))

        for rid in obj.get('remote_ids', []):
            remote_ids.append(RemoteId(
                movies=movie,
                remote_id=str(rid.get('remote_id', ''))[:200],
                id_type=rid.get('id_type', 0),
                source_name=rid.get('source_name', '')[:100],
            ))

        for c in obj.get('characters', []):
            person = get_or_create_person(
                c.get('person_tvdb_id', 0),
                (c.get('person_name', '') or '')[:300],
                (c.get('person_image', '') or '')[:1000]
            )
            characters.append(Character(
                tvdb_id=c.get('tvdb_id', 0),
                movies=movie,
                person=person,
                character_name=(c.get('character_name', '') or '')[:300],
                character_image=(c.get('character_image', '') or '')[:1000],
                people_type=(c.get('people_type', 'Actor') or 'Actor')[:50],
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
