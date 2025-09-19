from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Sequence

from .models import Post
from .scrapers.base import Scraper

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CollectionReport:
    posts: List[Post]
    errors: List[str]


class SentimentCollector:
    """Runs multiple scrapers in parallel and aggregates their results."""

    def __init__(self, scrapers: Sequence[Scraper]) -> None:
        self._scrapers = list(scrapers)

    async def collect(self, topic: str, limit: int) -> CollectionReport:
        tasks = [asyncio.create_task(scraper.fetch(topic, limit)) for scraper in self._scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        posts: List[Post] = []
        errors: List[str] = []

        for scraper, result in zip(self._scrapers, results, strict=False):
            if isinstance(result, Exception):
                message = f"{scraper.name} scraper failed: {result}"
                logger.warning(message)
                errors.append(message)
                continue

            posts.extend(result)

        return CollectionReport(posts=posts, errors=errors)

    def collect_sync(self, topic: str, limit: int) -> CollectionReport:
        return asyncio.run(self.collect(topic, limit))
