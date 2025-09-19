from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

from .collector import SentimentCollector
from .output import write_csv, write_json
from .scrapers import FacebookScraper, RedditScraper, TwitterScraper


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape social content for sentiment analysis.")
    parser.add_argument("topic", help="Topic or keyword to search for")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of posts to collect from each source")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["reddit", "twitter", "facebook"],
        default=["reddit"],
        help="Sources to include in the scrape",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Defaults to ./<topic>.<format>",
    )
    parser.add_argument(
        "--twitter-accounts",
        type=Path,
        help="Path to a JSON file with twscrape account credentials",
    )
    parser.add_argument(
        "--twitter-language",
        default=None,
        help="Restrict Twitter search to a specific language (ISO code)",
    )
    parser.add_argument(
        "--facebook-pages",
        nargs="+",
        help="Specific Facebook page handles to scrape",
    )
    parser.add_argument(
        "--facebook-cookies",
        type=Path,
        help="Optional path to a cookies JSON file for Facebook",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    scrapers = []
    if "reddit" in args.sources:
        scrapers.append(RedditScraper())

    if "twitter" in args.sources:
        if args.twitter_accounts:
            scrapers.append(TwitterScraper.from_accounts_file(args.twitter_accounts, language=args.twitter_language))
        else:
            scrapers.append(TwitterScraper(language=args.twitter_language))

    if "facebook" in args.sources:
        pages = args.facebook_pages
        cookies = args.facebook_cookies
        scrapers.append(FacebookScraper(pages=pages, cookies_path=cookies))

    if not scrapers:
        parser.error("No scrapers configured")

    collector = SentimentCollector(scrapers)
    report = collector.collect_sync(args.topic, args.limit)

    output_path = args.output or Path(f"{args.topic}.{args.format}")
    output_path = output_path.expanduser().resolve()

    if args.format == "json":
        write_json(report.posts, output_path)
    else:
        write_csv(report.posts, output_path)

    logging.info("Saved %s posts to %s", len(report.posts), output_path)
    if report.errors:
        for error in report.errors:
            logging.warning(error)


if __name__ == "__main__":  # pragma: no cover
    main()
