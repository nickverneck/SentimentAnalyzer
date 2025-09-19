from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import Post


class Scraper(ABC):
    name: str

    @abstractmethod
    async def fetch(self, topic: str, limit: int) -> List[Post]:
        """Fetch posts for the topic."""


__all__ = ["Scraper"]
