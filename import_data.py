#!/usr/bin/env python
"""
Import large JSON.gz TVDB data into Django models.
Usage: python manage.py shell < import_data.py
Or: python import_data.py /path/to/data.json.gz
"""
import gzip
import json
import sys
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import transaction
from series.models import Series, Genre, SeriesGenre, RemoteId, Person, Character, TagOption

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
    
    series_batch = []
    processed = 0
    
    with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            obj = json.loads(line)
            if 'id' not in obj:
                continue
            
            series_batch.append(obj)
            
            if len(series_batch) >= BATCH_SIZE:
                process_batch(series_batch)
                processed += len(series_batch)
                print(f"  Processed {processed} series...")
                series_batch.clear()
        
        if series_batch:
            process_batch(series_batch)
            processed += len(series_batch)
            print(f"  Processed {processed} series total")
    
    print(f"Done! Imported {processed} series.")

def process_batch(batch):
    series_to_create = []
    raw_by_tvdb_id = {}
    
    for obj in batch:
        tvdb_id = obj.get('id')
        if not tvdb_id:
            continue
        
        series = Series(
            tvdb_id=tvdb_id,
            schema_version=obj.get('_schema', 1),
            name=(obj.get('name', '') or '')[:500],
            slug=(obj.get('slug', '') or '')[:500],
            image=(obj.get('image', '') or '')[:1000],
            year=(obj.get('year', '') or '')[:10],
            overview=obj.get('overview', '') or '',
            original_country=(obj.get('originalCountry', '') or '')[:100],
            original_language=(obj.get('originalLanguage', '') or '')[:50],
            status=(obj.get('status', '') or '')[:50],
            episode_count=obj.get('episodeCount', 0) or 0,
            season_count=obj.get('seasonCount', 0) or 0,
            rate=obj.get('rate'),
            name_en=(obj.get('name_en', '') or '')[:500],
            overview_en=obj.get('overview_en', '') or '',
            name_fa=(obj.get('name_fa', '') or '')[:500] if obj.get('name_fa') else None,
        )
        series_to_create.append(series)
        raw_by_tvdb_id[tvdb_id] = obj
    
    Series.objects.bulk_create(series_to_create, ignore_conflicts=True)
    
    saved_series = Series.objects.filter(tvdb_id__in=raw_by_tvdb_id.keys())
    series_map = {s.tvdb_id: s for s in saved_series}
    
    genre_links = []
    remote_ids = []
    characters = []
    tag_options = []
    
    for tvdb_id, obj in raw_by_tvdb_id.items():
        series = series_map.get(tvdb_id)
        if not series:
            continue
        
        for g in obj.get('genres', []):
            genre = get_or_create_genre(
                g.get('id', 0),
                g.get('name', ''),
                g.get('slug', '')
            )
            genre_links.append(SeriesGenre(series=series, genre=genre))
        
        for rid in obj.get('remoteIds', []):
            remote_ids.append(RemoteId(
                series=series,
                remote_id=str(rid.get('id', ''))[:200],
                id_type=rid.get('type', 0),
                source_name=rid.get('sourceName', '')[:100],
            ))
        
        for c in obj.get('characters', []):
            person = get_or_create_person(
                c.get('peopleId', 0),
                (c.get('personName', '') or '')[:300],
                (c.get('personImgURL', '') or '')[:1000]
            )
            characters.append(Character(
                tvdb_id=c.get('id', 0),
                series=series,
                person=person,
                character_name=(c.get('name', '') or '')[:300],
                character_image=(c.get('image', '') or '')[:1000],
                people_type=(c.get('peopleType', 'Actor') or 'Actor')[:50],
            ))
        
        for t in obj.get('tagOptions', []):
            tag_options.append(TagOption(
                series=series,
                tvdb_id=t.get('tvdb_id', 0),
                tag=t.get('tag', 0),
                tag_name=t.get('tag_name', '')[:200],
                name=t.get('name', '')[:200],
            ))
    
    SeriesGenre.objects.bulk_create(genre_links, ignore_conflicts=True)
    RemoteId.objects.bulk_create(remote_ids, ignore_conflicts=True)
    Character.objects.bulk_create(characters, ignore_conflicts=True)
    TagOption.objects.bulk_create(tag_options, ignore_conflicts=True)

if __name__ == '__main__':
    gz_path = sys.argv[1] if len(sys.argv) > 1 else 'data.json.gz'
    if not os.path.exists(gz_path):
        print(f"File not found: {gz_path}")
        sys.exit(1)
    import_file(gz_path)