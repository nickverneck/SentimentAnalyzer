from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from ..models import Post
from .base import Scraper


def _get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _loads_accounts(path: Path) -> List["TwitterAccount"]:
    data = json.loads(path.read_text(encoding="utf-8"))
    accounts: List[TwitterAccount] = []
    for entry in data:
        accounts.append(
            TwitterAccount(
                username=entry["username"],
                password=entry["password"],
                email=entry.get("email"),
                email_password=entry.get("email_password"),
            )
        )
    return accounts


@dataclass(slots=True)
class TwitterAccount:
    username: str
    password: str
    email: str | None = None
    email_password: str | None = None


class TwitterScraper(Scraper):
    name = "twitter"

    def __init__(self, accounts: Iterable[TwitterAccount] | None = None, language: str | None = None) -> None:
        self._accounts = list(accounts) if accounts else []
        self._language = language
        self._api = None
        self._logged_in = False

    @classmethod
    def from_accounts_file(cls, path: str | Path, language: str | None = None) -> "TwitterScraper":
        account_path = Path(path)
        if not account_path.exists():
            raise RuntimeError(f"Twitter accounts file not found: {account_path}")
        return cls(accounts=_loads_accounts(account_path), language=language)

    async def fetch(self, topic: str, limit: int) -> List[Post]:
        try:
            from twscrape import API
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install twscrape to use the Twitter scraper") from exc

        if self._api is None:
            self._api = API()

        await self._ensure_login()

        assert self._api is not None
        search_kwargs: Dict[str, Any] = {"limit": limit}
        if self._language:
            search_kwargs["lang"] = self._language

        tweets = self._api.search(topic, **search_kwargs)

        posts: List[Post] = []
        async for tweet in tweets:  # type: ignore[assignment]
            posts.append(self._to_post(tweet, topic))
            if len(posts) >= limit:
                break

        return posts

    async def _ensure_login(self) -> None:
        assert self._api is not None
        if self._logged_in:
            return
        pool = getattr(self._api, "pool", None)
        if pool is None:
            self._logged_in = True
            return

        if self._accounts:
            for account in self._accounts:
                await pool.add_account(
                    account.username,
                    account.password,
                    account.email,
                    account.email_password,
                )
        await pool.login_all()
        self._logged_in = True

    def _to_post(self, tweet: Any, topic: str) -> Post:
        created = _get(tweet, "date")
        created_at = created if isinstance(created, datetime) else None

        url = _get(tweet, "url")
        text = _get(tweet, "rawContent") or _get(tweet, "text") or ""
        user = _get(tweet, "user")
        username = _get(user, "username") if user else None

        metadata: Dict[str, Any] = {
            "retweets": _get(tweet, "retweetCount"),
            "likes": _get(tweet, "likeCount"),
            "replies": _get(tweet, "replyCount"),
            "quotes": _get(tweet, "quoteCount"),
        }

        identifier = str(_get(tweet, "id"))

        return Post(
            id=identifier,
            source=self.name,
            topic=topic,
            text=text,
            url=url,
            author=username,
            created_at=created_at,
            metadata={k: v for k, v in metadata.items() if v is not None},
        )


__all__ = ["TwitterScraper", "TwitterAccount"]
