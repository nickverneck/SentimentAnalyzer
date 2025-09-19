# Sentiment Analyzer Backend

Command-line toolkit for scraping Reddit, Twitter, and Facebook content for a given topic. The normalized output can be saved as JSON or CSV, ready for downstream sentiment analysis by an LLM or other tooling.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management
- Platform credentials:
  - **Reddit:** OAuth credentials and account login
  - **Twitter:** twscrape-compatible account credentials
  - **Facebook:** Page list (and cookies file if needed)

## Installation

```bash
uv sync
```

> **Note:** `yars` is sourced from `https://github.com/datavorous/yars`. Ensure git access is available when syncing dependencies.

This creates a virtual environment at `.venv`. Activate it with `source .venv/bin/activate` (or use `uv run`/`uvx` shortcuts).

## Configuration

### Reddit
Set the following environment variables before running the scraper:

```bash
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USERNAME=...
export REDDIT_PASSWORD=...
export REDDIT_USER_AGENT="sentiment-analyzer/0.1"
```

### Twitter (twscrape)
Create a JSON file with account credentials accepted by `twscrape`:

```json
[
  {
    "username": "handle",
    "password": "account-password",
    "email": "optional-email",
    "email_password": "optional-email-password"
  }
]
```

Pass the file path via `--twitter-accounts`. If omitted, `twscrape` will use any accounts previously stored in its local database.

### Facebook
Specify the pages to scan either via CLI (`--facebook-pages`) or environment variable:

```bash
export FACEBOOK_PAGES="nytimes,bbcnews"
```

If you need authenticated scraping, provide a cookies JSON file (exported via browser extensions) through `--facebook-cookies` or by setting `FACEBOOK_COOKIES` to the file path.

## Usage

```bash
uv run sentiment-analyzer "machine learning" \
  --limit 25 \
  --sources reddit twitter facebook \
  --format json \
  --output data/machine-learning.json \
  --twitter-accounts config/twitter_accounts.json \
  --facebook-pages theverge wired
```

- `--format` accepts `json` or `csv`.
- `--limit` applies per source.
- Omitting `--output` defaults to `./<topic>.<format>`.

Run `uv run sentiment-analyzer --help` to see all options.

## Next Steps

- Add additional media outlets by creating new scraper classes in `src/sentiment_analyzer/scrapers`.
- Feed the exported dataset into your LLM workflow for sentiment scoring.
- Extend the collector with retry or scheduling capabilities as deployment needs evolve.
