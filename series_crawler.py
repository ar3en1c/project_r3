import gzip
import json
import logging
import os
import time

import requests
from decouple import config

# ─── Config ────────────────────────────────────────────────
API_KEY = config("TVDB_API_KEY")
BASE_URL = "https://api4.thetvdb.com/v4"
OUTPUT_FILE = "tvdb_data.jsonl.gz"
DONE_FILE = "done.txt"
FAILED_FILE = "failed.txt"
DAILY_LIMIT = 100000
SCHEMA_VERSION = 1

ALL_IDS = list(range(1, 900000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ─── Auth ───────────────────────────────────────────────────
def get_token():
    res = requests.post(f"{BASE_URL}/login", json={"apikey": API_KEY})
    res.raise_for_status()
    return res.json()["data"]["token"]


def make_session(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


def refresh_token_if_needed(session, last_token_time):
    """Refresh token every 20 hours to avoid 401 errors."""
    if time.time() - last_token_time > 20 * 3600:
        log.info("Refreshing token...")
        token = get_token()
        session.headers.update({"Authorization": f"Bearer {token}"})
        return time.time()
    return last_token_time


# ─── Progress tracking ──────────────────────────────────────
def load_done():
    if not os.path.exists(DONE_FILE):
        return set()
    with open(DONE_FILE) as f:
        return set(int(x) for x in f.read().splitlines() if x.strip())


def mark_done(series_id):
    with open(DONE_FILE, "a") as f:
        f.write(f"{series_id}\n")


def mark_failed(series_id):
    with open(FAILED_FILE, "a") as f:
        f.write(f"{series_id}\n")


# ─── Data extraction ────────────────────────────────────────
def get_english(items, field):
    """Return the English value of a field from a translations list."""
    for item in (items or []):
        if item.get("language") == "eng":
            return item.get(field)
    return None


def extract(d):
    """Extract and normalize fields, preferring English translations."""
    trans = d.get("translations") or {}
    name = d.get("name")
    overview = d.get("overview")

    # Override name/overview with English translation if original is not English
    if d.get("originalLanguage") != "eng":
        name = get_english(trans.get("nameTranslations"), "name") or name
        overview = get_english(trans.get("overviewTranslations"), "overview") or overview

    return {
        "_schema": SCHEMA_VERSION,
        "id": d.get("id"),
        "name": name,
        "slug": d.get("slug"),
        "image": d.get("image"),
        "year": d.get("year"),
        "overview": overview,
        "originalCountry": d.get("originalCountry"),
        "originalLanguage": d.get("originalLanguage"),
        "genres": [
            {"id": g["id"], "name": g["name"], "slug": g["slug"]}
            for g in (d.get("genres") or [])
        ],
        "remoteIds": [
            {"id": r["id"], "type": r["type"], "sourceName": r["sourceName"]}
            for r in (d.get("remoteIds") or [])
        ],
        "characters": [
            {
                "id": c["id"],
                "name": c.get("name"),
                "image": c.get("image"),
                "peopleId": c.get("peopleId"),
                "peopleType": c.get("peopleType"),
                "personName": c.get("personName"),
                "personImgURL": c.get("personImgURL"),
            }
            for c in (d.get("characters") or [])
        ],
        "tagOptions": [
            {"id": t["id"], "tag": t["tag"], "tagName": t["tagName"], "name": t["name"]}
            for t in (d.get("tags") or [])
        ],
    }


# ─── API call ───────────────────────────────────────────────
def get_series(session, series_id):
    res = session.get(f"{BASE_URL}/series/{series_id}/extended?meta=translations")
    res.raise_for_status()
    return res.json()["data"]


# ─── Output ─────────────────────────────────────────────────
def save(data):
    with gzip.open(OUTPUT_FILE, "at", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


# ─── Main ───────────────────────────────────────────────────
if __name__ == "__main__":
    token = get_token()
    session = make_session(token)
    last_token_time = time.time()

    done_set = load_done()
    remaining = [i for i in ALL_IDS if i not in done_set]
    batch = remaining[:DAILY_LIMIT]

    log.info(f"Remaining: {len(remaining)} | Today's batch: {len(batch)}")

    for series_id in batch:
        last_token_time = refresh_token_if_needed(session, last_token_time)

        try:
            raw = get_series(session, series_id)
            filtered = extract(raw)
            save(filtered)
            mark_done(series_id)
            log.info(f"OK  {series_id} - {filtered.get('name', 'N/A')}")

        except requests.HTTPError as e:
            status = e.response.status_code
            if status == 404:
                # 404 means the series doesn't exist, skip it
                mark_done(series_id)
                log.warning(f"SKIP {series_id} - 404 not found")
            elif status == 401:
                # Token expired mid-batch, refresh and continue
                log.warning(f"AUTH {series_id} - 401, refreshing token...")
                token = get_token()
                session.headers.update({"Authorization": f"Bearer {token}"})
                last_token_time = time.time()
            else:
                mark_failed(series_id)
                log.error(f"FAIL {series_id} - HTTP {status}")

        except Exception as e:
            mark_failed(series_id)
            log.error(f"FAIL {series_id} - {e}")

        time.sleep(1)

    log.info(f"Batch complete. Processed: {len(batch)}")

