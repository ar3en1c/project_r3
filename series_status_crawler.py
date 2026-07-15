import gzip
import json
import logging
import os
import time

import requests
from decouple import config

API_KEY = config("TVDB_API_KEY")
BASE_URL = "https://api4.thetvdb.com/v4"
OUTPUT_FILE = "series_status.jsonl.gz"
DONE_FILE = "status_done.txt"
FAILED_FILE = "status_failed.txt"
DAILY_LIMIT = 100000

ALL_IDS = list(range(1, 900000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("status_crawler.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def get_token():
    res = requests.post(f"{BASE_URL}/login", json={"apikey": API_KEY})
    res.raise_for_status()
    return res.json()["data"]["token"]


def make_session(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


def refresh_token_if_needed(session, last_token_time):
    if time.time() - last_token_time > 20 * 3600:
        log.info("Refreshing token...")
        token = get_token()
        session.headers.update({"Authorization": f"Bearer {token}"})
        return time.time()
    return last_token_time


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


def extract_status(d):
    status = d.get("status")
    if isinstance(status, dict):
        status = status.get("name") or status.get("id")
    return {
        "id": d.get("id"),
        "status": status,
        "season_count": len(d.get("seasons") or []),
        "episode_count": len(d.get("episodes") or []),
    }


def get_series(session, series_id):
    res = session.get(f"{BASE_URL}/series/{series_id}/extended")
    res.raise_for_status()
    return res.json()["data"]


def save(data):
    with gzip.open(OUTPUT_FILE, "at", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


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
            filtered = extract_status(raw)
            save(filtered)
            mark_done(series_id)
            log.info(f"OK  {series_id} - {filtered.get('status', 'N/A')}")

        except requests.HTTPError as e:
            status = e.response.status_code
            if status == 404:
                mark_done(series_id)
                log.warning(f"SKIP {series_id} - 404 not found")
            elif status == 401:
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
