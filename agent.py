#!/usr/bin/env python3
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import List
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import feedparser
import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path(__file__).with_name(".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)


@dataclass
class Article:
    title: str
    link: str
    published: str
    snippet: str = ""


def summarize(text):
    response = client.chat.completions.create(
        model="z-ai/glm-5.1",
        messages=[
            {"role": "system", "content": "Summarize in 2 short lines."},
            {"role": "user", "content": text}
        ],
        temperature=0.3,
        max_tokens=100
    )
    return response.choices[0].message.content.strip()


def clean_text(value: str) -> str:
    return " ".join(unescape(value or "").replace("\xa0", " ").split())


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "url" in query and query["url"]:
        return unquote(query["url"][0])
    return url


def format_date(value: str) -> str:
    if not value:
        return "Unknown date"
    for pattern in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, pattern).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return value


def request_with_retry(url: str, retries: int = 3, timeout: int = 20) -> bytes:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ai-news-agent/1.0)"}
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            last_error = exc
            print(f"Fetch attempt {attempt}/{retries} failed: {exc}")
    raise RuntimeError(f"Unable to fetch RSS feed: {last_error}")


def fetch_news(limit: int = 10) -> List[Article]:
    print("Fetching news...")
    rss_url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus('Artificial Intelligence')}&hl=en-US&gl=US&ceid=US:en"
    )
    feed = feedparser.parse(request_with_retry(rss_url))
    articles: List[Article] = []
    seen_urls = set()
    seen_titles = set()

    for entry in feed.entries:
        title = clean_text(getattr(entry, "title", ""))
        if " - " in title:
            title = title.rsplit(" - ", 1)[0].strip()
        link = normalize_url(getattr(entry, "link", ""))
        published = format_date(getattr(entry, "published", ""))
        snippet = clean_text(getattr(entry, "summary", ""))

        if not title or not link:
            continue
        if link.lower() in seen_urls or title.lower() in seen_titles:
            continue

        seen_urls.add(link.lower())
        seen_titles.add(title.lower())
        articles.append(
            Article(
                title=title,
                link=link,
                published=published,
                snippet=snippet,
            )
        )
        if len(articles) >= limit:
            break

    return articles


def build_summary_input(article: Article) -> str:
    if article.snippet:
        return f"{article.title}\n\n{article.snippet}"
    return article.title


def build_message(articles: List[Article]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    if not articles:
        return f"*🧠 Daily AI News ({today})*\n\nNo AI news today"

    lines = [f"*🧠 Daily AI News ({today})*"]
    print("Summarizing...")
    for index, article in enumerate(articles, start=1):
        print(f"  {index}/{len(articles)}")
        try:
            summary = summarize(build_summary_input(article))
        except Exception as exc:
            print(f"LLM failed for '{article.title}': {exc}")
            summary = article.title

        lines.append(
            f"\n{index}. *{article.title}*\n"
            f"<{article.link}>\n"
            f"{summary}\n"
            f"_Published: {article.published}_"
        )
    return "\n".join(lines)


def send_to_slack(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("Slack error: Missing SLACK_WEBHOOK_URL")
        return

    response = requests.post(
        webhook_url,
        json={"text": message},
        timeout=20,
    )

    if response.status_code != 200:
        print("Slack error:", response.text)
    else:
        print("✅ Sent to Slack successfully")


def main() -> None:
    try:
        articles = fetch_news(limit=int(os.getenv("MAX_ARTICLES", "10")))
    except Exception as exc:
        print(f"Failed to fetch news: {exc}")
        articles = []

    message = build_message(articles)

    print("Sending to Slack...")
    send_to_slack(message)

    print("Done")


if __name__ == "__main__":
    main()
