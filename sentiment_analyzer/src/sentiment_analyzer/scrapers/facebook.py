from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from ..models import Post
from .base import Scraper


def _get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


class FacebookScraper(Scraper):
    name = "facebook"

    def __init__(self, pages: Sequence[str] | None = None, cookies_path: str | Path | None = None) -> None:
        self._pages = list(pages) if pages else self._pages_from_env()
        self._cookies_path = Path(cookies_path) if cookies_path else self._cookies_from_env()
        if not self._pages:
            raise RuntimeError("At least one Facebook page must be configured")

    @staticmethod
    def _pages_from_env() -> List[str]:
        pages = os.environ.get("FACEBOOK_PAGES", "")
        return [page.strip() for page in pages.split(",") if page.strip()]

    @staticmethod
    def _cookies_from_env() -> Path | None:
        cookies = os.environ.get("FACEBOOK_COOKIES")
        return Path(cookies) if cookies else None

    async def fetch(self, topic: str, limit: int) -> List[Post]:
        try:
            from facebook_scraper import get_posts
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install facebook-scraper to use the Facebook scraper") from exc

        cookies = self._load_cookies()
        topic_lower = topic.lower()
        collected: List[Post] = []

        async def _fetch_page(page: str) -> List[Dict[str, Any]]:
            def _run() -> List[Dict[str, Any]]:
                matches: List[Dict[str, Any]] = []
                for post in get_posts(page, cookies=cookies, page_limit=5, extra_info=True):
                    text = post.get("text") or ""
                    if topic_lower in text.lower():
                        matches.append(post)
                    if len(matches) >= limit:
                        break
                return matches

            return await asyncio.to_thread(_run)

        for page in self._pages:
            raw_posts = await _fetch_page(page)
            for raw in raw_posts:
                collected.append(self._to_post(raw, topic, page))
                if len(collected) >= limit:
                    return collected[:limit]

        return collected[:limit]

    def _load_cookies(self) -> Dict[str, Any] | None:
        if not self._cookies_path:
            return None
        if not self._cookies_path.exists():
            raise RuntimeError(f"Facebook cookies file not found: {self._cookies_path}")
        return json.loads(self._cookies_path.read_text(encoding="utf-8"))

    def _to_post(self, post: Mapping[str, Any], topic: str, page: str) -> Post:
        created = _get(post, "time")
        created_at = created if isinstance(created, datetime) else None
        metadata: Dict[str, Any] = {
            "likes": _get(post, "likes"),
            "comments": _get(post, "comments"),
            "shares": _get(post, "shares"),
            "page": page,
        }

        return Post(
            id=str(_get(post, "post_id")),
            source=self.name,
            topic=topic,
            text=_get(post, "text") or "",
            url=_get(post, "post_url"),
            author=_get(post, "user_id"),
            created_at=created_at,
            metadata={k: v for k, v in metadata.items() if v is not None},
        )


__all__ = ["FacebookScraper"]
