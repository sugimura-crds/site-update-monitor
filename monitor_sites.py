import csv
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

from urllib.parse import urljoin

RSS_CSV = "rss_sites.csv"
NO_RSS_CSV = "no_rss_sites.csv"

STATE_PATH = Path("state.json")
FEED_PATH = Path("docs/feed.xml")

MAX_ITEMS = 30


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def load_csv(path):
    rows = []

    encodings = ["utf-8-sig", "utf-8", "cp932"]

    last_error = None

    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    category = (row.get("Category") or "").strip()
                    url = (row.get("URL") or "").strip()
                    selector = (row.get("Selector") or "").strip()

                    if category and url:
                        rows.append({
                            "category": category,
                            "url": url,
                            "selector": selector
                        })

            print(f"Loaded {path} with encoding {enc}")
            return rows

        except UnicodeDecodeError as e:
            last_error = e
            rows = []

    raise last_error

def clean_text(text, max_len=300):
    text = " ".join((text or "").split())
    return text[:max_len]


def check_rss_feed(category, feed_url, state):
    parsed = feedparser.parse(feed_url)

    new_items = []

    for entry in parsed.entries[:5]:
        title = clean_text(entry.get("title", "No title"), 200)
        link = entry.get("link", "")
        summary = clean_text(
            BeautifulSoup(
                entry.get("summary", ""),
                "html.parser"
            ).get_text(" "),
            400
        )
        summary = re.sub(
            r"^Nature.*?doi:[^ ]+\s*",
            "",
            summary
        )

        published = (
            entry.get("published")
            or entry.get("updated")
            or datetime.now(timezone.utc).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )
        )

        guid = entry.get("id") or link or title

        key = f"rss::{guid}"

        if key not in state:
            state[key] = published

            new_items.append({
                "title": title,
                "link": link,
                "summary": summary,
                "published": published,
                "category": category,
                "source": feed_url
            })

    return new_items

def check_no_rss_site(category, url, selector, state):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    if not r.encoding or r.encoding.lower() in ["iso-8859-1", "windows-1252"]:
        r.encoding = r.apparent_encoding

    soup = BeautifulSoup(r.text, "html.parser")

    targets = []

    if selector:
        targets = soup.select(selector)

    if targets:
        target = targets[0]
    else:
        target = soup.find("main") or soup.body or soup

    for tag in target(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()

    a_tags = target.find_all("a", href=True)

    article_link = url

    for a in a_tags:
        href = a["href"]

        if href.startswith("mailto:"):
            continue

        if "/article" in href or "/articles/" in href:
            article_link = urljoin(url, href)
            break

        if href.startswith("http"):
            article_link = href
            break

    text = clean_text(target.get_text(" "), 1000)

    h = target.find(["h1", "h2", "h3", "a"])

    title = ""

    if h:
        title = clean_text(h.get_text(" "), 120)

    if not title:
        title = clean_text(text, 120)

    if not title:
        title = (
            soup.title.get_text(strip=True)
            if soup.title
            else url
        )

    p = target.find("p")

    summary = ""

    if p:
        summary = clean_text(p.get_text(" "), 600)

    if not summary:
        summary = clean_text(text, 600)
    
    digest_base = article_link + text

    digest = hashlib.sha256(
        digest_base.encode("utf-8")
    ).hexdigest()

    key = f"site::{url}"

    old_digest = state.get(key)

    state[key] = digest

    if old_digest is None:
        return None

    if old_digest != digest:
        return {
            "title": title,
            "link": article_link,
            "summary": summary,
            "published": datetime.now(timezone.utc).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            ),
            "category": category,
            "source": url
        }

    return None


def make_item_xml(item):
    title = f"【{item['category']}】 {item['title']}"

    description = html.escape(item["summary"])

    guid = hashlib.sha256(
        (item["link"] + item["published"]).encode("utf-8")
    ).hexdigest()

    return f"""
<item>
<title>{html.escape(title)}</title>
<link>{html.escape(item['link'])}</link>
<guid>{guid}</guid>
<pubDate>{item['published']}</pubDate>
<description>{description}</description>
</item>
""".strip()


def write_feed(items):
    now = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    item_xml = "\n".join(
        make_item_xml(item)
        for item in items[:MAX_ITEMS]
    )

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Site Update Monitor</title>
<link>https://github.com/</link>
<description>Site monitoring feed</description>
<lastBuildDate>{now}</lastBuildDate>

{item_xml}

</channel>
</rss>
"""

    FEED_PATH.write_text(feed, encoding="utf-8")


def main():
    state = load_state()

    rss_sites = load_csv(RSS_CSV)
    no_rss_sites = load_csv(NO_RSS_CSV)

    new_items = []

    for row in rss_sites:
        try:
            new_items.extend(
                check_rss_feed(
                    row["category"],
                    row["url"],
                    state
                )
            )
        except Exception as e:
            print(f"RSS ERROR {row['url']} {e}")

    for row in no_rss_sites:
        try:
            item = check_no_rss_site(
                row["category"],
                row["url"],
                row.get("selector", ""),
                state
            )

            if item:
                new_items.append(item)

        except Exception as e:
            print(f"SITE ERROR {row['url']} {e}")

    save_state(state)
    
    if not new_items:
        print("No new items")
        return

    write_feed(new_items)

    print(f"{len(new_items)} items updated")


if __name__ == "__main__":
    main()
