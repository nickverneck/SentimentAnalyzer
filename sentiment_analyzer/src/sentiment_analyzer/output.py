from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import Post


def write_json(posts: Iterable[Post], path: Path) -> None:
    data = [post.as_dict() for post in posts]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(posts: Iterable[Post], path: Path) -> None:
    rows = [post.as_csv_row() for post in posts]
    fieldnames = ["id", "source", "topic", "text", "url", "author", "created_at", "metadata"]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
