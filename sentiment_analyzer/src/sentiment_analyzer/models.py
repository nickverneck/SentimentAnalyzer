from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass(slots=True)
class Post:
    """Normalized representation of a social post."""

    id: str
    source: str
    topic: str
    text: str
    url: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "topic": self.topic,
            "text": self.text,
            "url": self.url,
            "author": self.author,
            "metadata": self.metadata or {},
        }
        if self.created_at is not None:
            data["created_at"] = self.created_at.isoformat()
        else:
            data["created_at"] = None
        return data

    def as_csv_row(self) -> Dict[str, Any]:
        row = self.as_dict()
        metadata = row.pop("metadata", {})
        row["metadata"] = metadata if isinstance(metadata, str) else str(metadata)
        return row
