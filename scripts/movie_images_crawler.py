"""
Movie image and overview crawler - minimal version

Fetches only:
- TVDB ID
- Movie image URL (poster)
- Overview (Persian if available, else English)

Usage: python scripts/movie_images_crawler.py
"""
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

OUTPUT_FILE = "tvdb_movie_images.jsonl.gz"
DONE_FILE = "movie_images_done.txt"
FAILED_FILE = "movie_images_failed.txt"

MIN_ID = 1
MAX_ID = 194351  # inclusive

REQUEST_DELAY = 1.0  # seconds between requests
MAX_RETRIES_ON_429 = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("movie_images_crawler.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
if hasattr(sys, 'stdout') and hasattr(sys.stdout, 'encoding'):
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

log = logging.getLogger(__name__)


def get_token():
    """Get TVDB API token."""
    data = request_json("POST", f"{BASE_URL}/login", {"apikey": API_KEY})
    return data["data"]["token"]


def make_headers(token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {token}"}


def request_json(method, url, payload=None, headers=None, params=None):
    """Make API request and return JSON response."""
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


def load_processed_ids():
    """Load already processed movie IDs."""
    if not os.path.exists(DONE_FILE):
        return set()
    with open(DONE_FILE, encoding="utf-8") as f:
        return set(int(x) for x in f.read().splitlines() if x.strip())


def mark_done(movie_id):
    """Mark movie as successfully processed."""
    with open(DONE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{movie_id}\n")


def mark_failed(movie_id):
    """Mark movie as failed."""
    with open(FAILED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{movie_id}\n")


def get_movie_minimal(headers, movie_id):
    """Get minimal movie data from TVDB API."""
    res = request_json(
        "GET",
        f"{BASE_URL}/movies/{movie_id}/extended",
        headers=headers,
        params={"meta": "translations"},
    )
    return res["data"]


def extract_minimal_data(movie):
    """Extract only the fields we need: image, overview, tvdb_id."""
    # Get Persian overview if available, else English, else original
    overview = None
    translations = movie.get("translations", {})

    # Check for Persian overview
    for item in translations.get("overviewTranslations", []):
        if item.get("language") == "per":
            overview = item.get("overview")
            break

    # Fallback to English if no Persian
    if not overview:
        for item in translations.get("overviewTranslations", []):
            if item.get("language") == "eng":
                overview = item.get("overview")
                break

    # Final fallback to original overview
    if not overview:
        overview = movie.get("overview")

    # TVDB v4 movie records use the "image" field for the poster URL
    # (there is no "poster" or "thumbnail" field on movie base/extended records)
    image = movie.get("image") or ""

    return {
        "tvdb_id": movie.get("id"),
        "image": image,
        "overview": overview,
    }


def save_data(data):
    """Save extracted data to output file."""
    with gzip.open(OUTPUT_FILE, "at", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def get_movie_ids_to_process():
    """Get list of movie IDs that need processing (fixed range, no DB dependency)."""
    processed_ids = load_processed_ids()
    all_ids = range(MIN_ID, MAX_ID + 1)
    return [i for i in all_ids if i not in processed_ids]


def fetch_with_backoff(headers, movie_id):
    """GET movie data, retrying on 429 with exponential backoff / Retry-After."""
    attempt = 0
    while True:
        try:
            return get_movie_minimal(headers, movie_id)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES_ON_429:
                retry_after = e.headers.get("Retry-After")
                if retry_after:
                    wait = float(retry_after)
                else:
                    wait = min(60, 5 * (2 ** attempt))  # 5, 10, 20, 40, 60...
                attempt += 1
                log.warning(f"429 for {movie_id} - backing off {wait}s (attempt {attempt})")
                time.sleep(wait)
                continue
            raise


def crawl_movie_images():
    """Main crawler function."""
    token = get_token()
    headers = make_headers(token)
    last_token_time = time.time()

    # Get movie IDs that need processing (entire remaining range in one run)
    movie_ids = get_movie_ids_to_process()

    log.info(f"Movies to process: {len(movie_ids)}")

    for movie_id in movie_ids:
        try:
            # Refresh token every 20 hours to avoid 401 errors
            if time.time() - last_token_time > 20 * 3600:
                log.info("Refreshing token...")
                token = get_token()
                headers.update(make_headers(token))
                last_token_time = time.time()

            # Get movie data (with automatic 429 backoff)
            raw = fetch_with_backoff(headers, movie_id)
            filtered = extract_minimal_data(raw)

            # Only save if we got an image or overview
            if filtered["image"] or filtered["overview"]:
                save_data(filtered)
                mark_done(movie_id)
                log.info(f"OK {movie_id} - Image: {'✓' if filtered['image'] else '✗'} Overview: {'✓' if filtered['overview'] else '✗'}")
            else:
                log.info(f"SKIP {movie_id} - No image or overview found")
                mark_done(movie_id)

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

        time.sleep(REQUEST_DELAY)  # Rate limiting

    log.info(f"Run complete. Processed: {len(movie_ids)}")


if __name__ == "__main__":
    crawl_movie_images()