import gzip
import http.client
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from decouple import config

# Config
API_KEY = config("TVDB_API_KEY")
BASE_URL = "https://api4.thetvdb.com/v4"

OUTPUT_FILE = "tvdb_movies.jsonl.gz"
DONE_FILE = "done.txt"
FAILED_FILE = "failed.txt"
DAILY_LIMIT = 100000

# TVDB movie ids are sparse. This scans possible ids and treats 404 as done.
ALL_IDS = list(range(1, 900000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("crawler.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# Auth
def get_token():
    data = request_json("POST", f"{BASE_URL}/login", {"apikey": API_KEY})
    return data["data"]["token"]


def make_headers(token):
    return {"Authorization": f"Bearer {token}"}


def refresh_token_if_needed(headers, last_token_time):
    """Refresh token every 20 hours to avoid 401 errors."""
    if time.time() - last_token_time > 20 * 3600:
        log.info("Refreshing token...")
        token = get_token()
        headers.update(make_headers(token))
        return time.time()
    return last_token_time


def request_json(method, url, payload=None, headers=None, params=None):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    body = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


# Progress tracking
def load_done():
    if not os.path.exists(DONE_FILE):
        return set()
    with open(DONE_FILE, encoding="utf-8") as f:
        return set(int(x) for x in f.read().splitlines() if x.strip())


def mark_done(movie_id):
    with open(DONE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{movie_id}\n")


def mark_failed(movie_id):
    with open(FAILED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{movie_id}\n")


# API calls
def get_movie(headers, movie_id):
    res = request_json(
        "GET",
        f"{BASE_URL}/movies/{movie_id}/extended",
        headers=headers,
        params={"meta": "translations"},
    )
    return res["data"]


# Data extraction
def get_translation(items, field, language):
    """Return the value of a field for a specific language from a translations list."""
    for item in items or []:
        if item.get("language") == language:
            return item.get(field)
    return None


def extract_movie(movie):
    translations = movie.get("translations") or {}
    original_lang = movie.get("originalLanguage", "")
    year = movie.get("year", "")

    # Original name and overview
    name = movie.get("name")
    overview = movie.get("overview")

    # English translations
    if original_lang == "eng":
        name_en = name
        overview_en = overview
    else:
        name_en = get_translation(translations.get("nameTranslations"), "name", "eng")
        overview_en = get_translation(
            translations.get("overviewTranslations"), "overview", "eng"
        )

    # Image: use poster if available, fallback to thumbnail, else empty
    image = movie.get("poster") or movie.get("thumbnail") or ""

    # Slug: append year to avoid collisions
    slug = movie.get("slug", "")
    if year:
        slug = f"{slug}-{year}"

    return {
        "tvdb_id": movie.get("id"),
        "schema_version": 1,
        "name": name,
        "slug": slug,
        "image": image,
        "year": year,
        "overview": overview,
        "original_country": movie.get("originalCountry"),
        "original_language": original_lang,
        "status": "Released",
        "rate": None,
        "name_en": name_en,
        "overview_en": overview_en,
        "name_fa": None,
        "genres": [
            {
                "tvdb_id": genre.get("id"),
                "name": genre.get("name"),
                "slug": genre.get("slug"),
            }
            for genre in movie.get("genres") or []
        ],
        "remote_ids": [
            {
                "remote_id": str(remote_id.get("id")),
                "id_type": remote_id.get("type"),
                "source_name": remote_id.get("sourceName"),
            }
            for remote_id in movie.get("remoteIds") or []
        ],
        "characters": [
            {
                "tvdb_id": character.get("id"),
                "character_name": character.get("name"),
                "character_image": character.get("image"),
                "people_type": character.get("peopleType"),
                "person_tvdb_id": character.get("peopleId"),
                "person_name": character.get("personName"),
                "person_image": character.get("personImgURL"),
            }
            for character in movie.get("characters") or []
        ],
    }


def save(data):
    with gzip.open(OUTPUT_FILE, "at", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def crawl_movies():
    token = get_token()
    headers = make_headers(token)
    last_token_time = time.time()

    done_set = load_done()
    remaining = [i for i in ALL_IDS if i not in done_set]
    batch = remaining[:DAILY_LIMIT]

    log.info(f"Remaining: {len(remaining)} | Today's batch: {len(batch)}")

    for movie_id in batch:
        last_token_time = refresh_token_if_needed(headers, last_token_time)

        try:
            raw = get_movie(headers, movie_id)
            filtered = extract_movie(raw)
            save(filtered)
            mark_done(movie_id)
            log.info(f"OK  {movie_id} - {filtered.get('name', 'N/A')}")

        except urllib.error.HTTPError as e:
            status = e.code
            if status == 404:
                mark_done(movie_id)
                log.warning(f"SKIP {movie_id} - 404 not found")
            elif status == 401:
                log.warning(f"AUTH {movie_id} - 401, refreshing token...")
                token = get_token()
                headers.update(make_headers(token))
                last_token_time = time.time()
            else:
                mark_failed(movie_id)
                log.error(f"FAIL {movie_id} - HTTP {status}")

        except (urllib.error.URLError, TimeoutError, http.client.HTTPException) as e:
            mark_failed(movie_id)
            log.error(f"FAIL {movie_id} - network error: {e}")

        except Exception as e:
            mark_failed(movie_id)
            log.error(f"FAIL {movie_id} - {e}")

        time.sleep(1)

    log.info(f"Batch complete. Processed: {len(batch)}")


if __name__ == "__main__":
    crawl_movies()
