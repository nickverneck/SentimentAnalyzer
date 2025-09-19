from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Mapping

from ..models import Post
from .base import Scraper


def _get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


@dataclass(slots=True)
class RedditCredentials:
    client_id: str
    client_secret: str
    username: str
    password: str
    user_agent: str


class RedditScraper(Scraper):
    name = "reddit"

    def __init__(self, credentials: RedditCredentials | None = None) -> None:
        self._credentials = credentials or self._credentials_from_env()
        self._validate_credentials()

    @staticmethod
    def _credentials_from_env() -> RedditCredentials:
        try:
            return RedditCredentials(
                client_id=os.environ["REDDIT_CLIENT_ID"],
                client_secret=os.environ["REDDIT_CLIENT_SECRET"],
                username=os.environ["REDDIT_USERNAME"],
                password=os.environ["REDDIT_PASSWORD"],
                user_agent=os.environ.get("REDDIT_USER_AGENT", "sentiment-analyzer/0.1"),
            )
        except KeyError as exc:  # pragma: no cover - environment dependent
            missing = exc.args[0]
            raise RuntimeError(f"Missing environment variable {missing} required for Reddit scraper") from exc

    def _validate_credentials(self) -> None:
        cred_dict = self._credentials.__dict__
        missing = [key for key, value in cred_dict.items() if not value]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Incomplete Reddit credentials: {joined}")

    async def fetch(self, topic: str, limit: int) -> List[Post]:
        try:
            from yars import Reddit
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install yars from https://github.com/datavorous/yars to use the Reddit scraper") from exc

        client = Reddit(
            client_id=self._credentials.client_id,
            client_secret=self._credentials.client_secret,
            username=self._credentials.username,
            password=self._credentials.password,
            user_agent=self._credentials.user_agent,
        )

        posts: List[Post] = []
        try:
            search = client.search(topic, limit=limit)  # type: ignore[attr-defined]

            if hasattr(search, "__aiter__"):
                async for submission in search:  # type: ignore[assignment]
                    posts.append(self._to_post(submission, topic))
                    if len(posts) >= limit:
                        break
            else:
                for submission in search:  # type: ignore[assignment]
                    posts.append(self._to_post(submission, topic))
                    if len(posts) >= limit:
                        break
        finally:
            closer = getattr(client, "close", None)
            if closer:
                if inspect.iscoroutinefunction(closer):
                    await closer()
                else:
                    closer()

        return posts

    def _to_post(self, submission: Any, topic: str) -> Post:
        created = _get(submission, "created_utc") or _get(submission, "created")
        created_at = datetime.fromtimestamp(created) if isinstance(created, (int, float)) else None
        url = _get(submission, "url") or _get(submission, "permalink")
        if url and not str(url).startswith("http"):
            url = f"https://www.reddit.com{url}"

        text = _get(submission, "selftext") or _get(submission, "body") or _get(submission, "title") or ""

        metadata: Dict[str, Any] = {
            "score": _get(submission, "score"),
            "subreddit": _get(submission, "subreddit"),
            "num_comments": _get(submission, "num_comments"),
        }

        identifier = _get(submission, "id") or _get(submission, "name") or url or text[:30]

        return Post(
            id=str(identifier),
            source=self.name,
            topic=topic,
            text=text,
            url=url,
            author=_get(submission, "author"),
            created_at=created_at,
            metadata={k: v for k, v in metadata.items() if v is not None},
        )
