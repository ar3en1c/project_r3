"""IMDb top-250 rank lookup from the CSVs in datas/."""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MOVIES_CSV = BASE_DIR / "datas" / "imdb_movies_top250.csv"
SERIES_CSV = BASE_DIR / "datas" / "imdb_series_top250.csv"


def _rank_map(path):
    with open(path, encoding="utf-8") as f:
        return {row["id"]: i for i, row in enumerate(csv.DictReader(f), 1)}


MOVIES_RANKS = _rank_map(MOVIES_CSV)
SERIES_RANKS = _rank_map(SERIES_CSV)
