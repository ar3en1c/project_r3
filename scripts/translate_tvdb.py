import gzip
import json
import time
import os
import sys
import argparse
import requests
from decouple import config

API_KEY = config("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "tencent/hy3:free"

INPUT_FILE = "tvdb_data.jsonl.gz"
OUTPUT_FILE = "tvdb_data_fa.jsonl.gz"
CHECKPOINT_FILE = "translate_checkpoint.json"
GENRES_FILE = "genres_fa.json"

DELAY_BETWEEN_REQUESTS = 1.5
MAX_RETRIES = 3
RETRY_DELAY = 10

SYSTEM_PROMPT = "You are a professional translator. Translate English text to natural Persian (Farsi). Return ONLY valid JSON, no markdown, no explanation. Keep proper nouns (names of people) as-is unless they have a known Persian equivalent. For series titles, transliterate to Persian."


def translate_text(texts: list[str], api_key: str) -> list[str]:
    if not texts or all(not t.strip() for t in texts):
        return texts

    numbered = "\n".join(f"[{i}] {t}" for i, t in enumerate(texts))
    user_msg = f"Translate these to Persian. Return a JSON array of translations in the same order, preserving [index]. Only output the JSON array, nothing else.\n\n{numbered}"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                },
                timeout=60,
            )
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", RETRY_DELAY * (attempt + 1)))
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(content)
            if isinstance(result, list) and len(result) == len(texts):
                return [str(r) for r in result]
            return texts
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                print(f"  Failed after {MAX_RETRIES} attempts: {e}")
                return texts
    return texts


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"last_line": 0}


def save_checkpoint(line_num):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"last_line": line_num}, f)


def load_genres():
    if os.path.exists(GENRES_FILE):
        with open(GENRES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_genres(genre_map):
    with open(GENRES_FILE, "w", encoding="utf-8") as f:
        json.dump(genre_map, f, ensure_ascii=False, indent=2)


def translate_record(record, genre_map, api_key):
    texts = []
    index_map = {}

    texts.append(record.get("name", ""))
    index_map["name"] = len(texts) - 1

    texts.append(record.get("overview", ""))
    index_map["overview"] = len(texts) - 1

    for ch in record.get("characters", []):
        if ch.get("personName"):
            texts.append(ch["personName"])
            index_map[f"actor_{ch['id']}"] = len(texts) - 1
        if ch.get("name"):
            texts.append(ch["name"])
            index_map[f"char_{ch['id']}"] = len(texts) - 1

    translated = translate_text(texts, api_key)

    record["tvdb_id"] = record.get("id")
    record["name"] = translated[index_map["name"]]
    record["overview_fa"] = translated[index_map["overview"]]

    for g in record.get("genres", []):
        if g["name"] in genre_map:
            g["name_fa"] = genre_map[g["name"]]

    for ch in record.get("characters", []):
        if ch.get("personName") and f"actor_{ch['id']}" in index_map:
            ch["personName_fa"] = translated[index_map[f"actor_{ch['id']}"]]
        if ch.get("name") and f"char_{ch['id']}" in index_map:
            ch["name_fa"] = translated[index_map[f"char_{ch['id']}"]]

    return record


def translate_missing_genres(genre_map, api_key):
    with gzip.open(INPUT_FILE, "rt", encoding="utf-8") as f:
        all_genres = set()
        for line in f:
            rec = json.loads(line)
            for g in rec.get("genres", []):
                all_genres.add(g["name"])

    missing = sorted(all_genres - set(genre_map.keys()))
    if not missing:
        print(f"All {len(genre_map)} genres already translated.")
        return genre_map

    print(f"Translating {len(missing)} new genres...")
    translated = translate_text(missing, api_key)
    for name, tr in zip(missing, translated):
        genre_map[name] = tr
        print(f"  {name} -> {tr}")

    save_genres(genre_map)
    return genre_map


def main():
    parser = argparse.ArgumentParser(description="Translate TVDB data to Persian")
    parser.add_argument("--test", type=int, default=0, help="Process only N lines (for testing)")
    parser.add_argument("--reset", action="store_true", help="Ignore checkpoint, start fresh")
    args = parser.parse_args()

    if args.reset:
        for f in [CHECKPOINT_FILE, OUTPUT_FILE]:
            if os.path.exists(f):
                os.remove(f)
        print("Checkpoint and output cleared.")

    genre_map = load_genres()
    genre_map = translate_missing_genres(genre_map, API_KEY)

    checkpoint = load_checkpoint()
    start_line = checkpoint["last_line"]

    mode = "ab" if start_line > 0 else "wb"
    out_f = gzip.open(OUTPUT_FILE, mode)
    in_f = gzip.open(INPUT_FILE, "rt", encoding="utf-8")

    total = 0
    limit = args.test if args.test > 0 else float("inf")
    for i, line in enumerate(in_f):
        if i < start_line:
            continue
        if total >= limit:
            break
        record = json.loads(line)
        translated = translate_record(record, genre_map, API_KEY)
        out_f.write((json.dumps(translated, ensure_ascii=False) + "\n").encode("utf-8"))
        out_f.flush()
        total += 1
        if total % 10 == 0:
            save_checkpoint(i + 1)
            print(f"Progress: {i + 1} lines processed, {total} translated this run")
        time.sleep(DELAY_BETWEEN_REQUESTS)

    save_checkpoint(i + 1)
    out_f.close()
    in_f.close()
    print(f"Done. Total translated: {total}")


if __name__ == "__main__":
    main()
