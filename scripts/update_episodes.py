#!/usr/bin/env python3
"""
Fetch new Generation AI episodes from the AZFamily YouTube channel RSS feed,
optionally scrape azfamily.com for the matching article link, and update
data/episodes.json.

Uses only Python standard library -- no pip install needed.
"""

import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
EPISODES_JSON = os.path.join(PROJECT_ROOT, "data", "episodes.json")

# AZFamily YouTube channel
CHANNEL_ID = "UCIrgpHvUm1FMtv-C1xwkJtw"
YOUTUBE_RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

AZFAMILY_TECH_URL = "https://www.azfamily.com/news/technology/"

# Namespaces used in the YouTube RSS feed
YT_NS = "http://www.youtube.com/xml/schemas/2015"
MEDIA_NS = "http://search.yahoo.com/mrss/"
ATOM_NS = "http://www.w3.org/2005/Atom"

GENAI_PATTERN = re.compile(r"generation\s+ai", re.IGNORECASE)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_url(url):
    """Fetch a URL and return the response body as a string."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_youtube_rss():
    """Fetch the YouTube RSS feed and return Generation AI episodes."""
    xml_text = fetch_url(YOUTUBE_RSS)
    root = ET.fromstring(xml_text)

    episodes = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        title_el = entry.find(f"{{{ATOM_NS}}}title")
        if title_el is None or title_el.text is None:
            continue

        title = title_el.text.strip()
        if not GENAI_PATTERN.search(title):
            continue

        video_id_el = entry.find(f"{{{YT_NS}}}videoId")
        published_el = entry.find(f"{{{ATOM_NS}}}published")

        if video_id_el is None or published_el is None:
            continue

        video_id = video_id_el.text.strip()
        published = published_el.text.strip()

        # Extract description from media:group > media:description
        description = ""
        media_group = entry.find(f"{{{MEDIA_NS}}}group")
        if media_group is not None:
            desc_el = media_group.find(f"{{{MEDIA_NS}}}description")
            if desc_el is not None and desc_el.text:
                # Take the first paragraph (before blank line or URL)
                raw = desc_el.text.strip()
                paragraphs = re.split(r"\n\s*\n", raw)
                if paragraphs:
                    first = paragraphs[0].strip()
                    # Stop at first URL-like line
                    lines = []
                    for line in first.split("\n"):
                        if re.match(r"https?://", line.strip()):
                            break
                        lines.append(line.strip())
                    description = " ".join(lines)

        # Parse the published date
        # Format: 2026-02-11T22:00:00+00:00
        date_str = published[:10]  # YYYY-MM-DD
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            date_formatted = dt.strftime("%B %d, %Y")
            # Remove leading zero from day: "February 05" -> "February 5"
            date_formatted = re.sub(r" 0(\d)", r" \1", date_formatted)
        except ValueError:
            date_formatted = date_str

        episodes.append({
            "title": title,
            "youtubeId": video_id,
            "date": date_str,
            "dateFormatted": date_formatted,
            "description": description,
        })

    return episodes


class AZFamilyLinkParser(HTMLParser):
    """Parse azfamily.com HTML to find Generation AI article links."""

    def __init__(self):
        super().__init__()
        self.links = []
        self._in_a = False
        self._current_href = ""
        self._current_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href:
                self._in_a = True
                self._current_href = href
                self._current_text = ""

    def handle_data(self, data):
        if self._in_a:
            self._current_text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._in_a:
            self._in_a = False
            href = self._current_href
            text = self._current_text.strip()
            # Check if this link is related to Generation AI
            if GENAI_PATTERN.search(text) or GENAI_PATTERN.search(href):
                self.links.append({
                    "href": href,
                    "text": text,
                })


def scrape_azfamily_links():
    """Scrape azfamily.com technology page for Generation AI article links."""
    try:
        html = fetch_url(AZFAMILY_TECH_URL)
        parser = AZFamilyLinkParser()
        parser.feed(html)
        return parser.links
    except Exception as e:
        print(f"Warning: Could not scrape azfamily.com: {e}", file=sys.stderr)
        return []


def match_article_url(episode_title, azfamily_links):
    """Try to match an episode to an AZFamily article link."""
    if not azfamily_links:
        return ""

    # Normalize the episode title for matching
    title_words = set(re.findall(r"\w+", episode_title.lower()))

    best_match = ""
    best_score = 0

    for link in azfamily_links:
        # Score by word overlap between episode title and link text/URL
        link_words = set(re.findall(r"\w+", (link["text"] + " " + link["href"]).lower()))
        overlap = len(title_words & link_words)
        if overlap > best_score:
            best_score = overlap
            best_match = link["href"]

    # Require at least 3 overlapping words to consider it a match
    if best_score >= 3:
        # Ensure it's a full URL
        if best_match.startswith("/"):
            best_match = "https://www.azfamily.com" + best_match
        return best_match

    return ""


def load_episodes():
    """Load existing episodes.json."""
    if os.path.exists(EPISODES_JSON):
        with open(EPISODES_JSON, "r") as f:
            return json.load(f)
    return {"lastUpdated": "", "episodes": []}


def save_episodes(data):
    """Write episodes.json."""
    with open(EPISODES_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    print(f"Fetching YouTube RSS feed for channel {CHANNEL_ID}...")
    yt_episodes = parse_youtube_rss()
    print(f"Found {len(yt_episodes)} Generation AI episode(s) in YouTube feed.")

    # Load existing data
    data = load_episodes()
    existing_ids = {ep["youtubeId"] for ep in data["episodes"]}

    # Scrape AZFamily (best-effort)
    print("Scraping azfamily.com for article links...")
    azfamily_links = scrape_azfamily_links()
    print(f"Found {len(azfamily_links)} Generation AI link(s) on azfamily.com.")

    # Find new episodes
    new_episodes = []
    for ep in yt_episodes:
        if ep["youtubeId"] in existing_ids:
            print(f"  Skipping (already exists): {ep['title']}")
            continue

        article_url = match_article_url(ep["title"], azfamily_links)

        new_ep = {
            "number": len(data["episodes"]) + len(new_episodes) + 1,
            "title": ep["title"],
            "guest": "",
            "date": ep["date"],
            "dateFormatted": ep["dateFormatted"],
            "description": ep["description"],
            "youtubeId": ep["youtubeId"],
            "azfamilyUrl": article_url,
        }
        new_episodes.append(new_ep)
        print(f"  New episode: {ep['title']}")
        if article_url:
            print(f"    AZFamily article: {article_url}")
        else:
            print("    No AZFamily article found (can be added manually)")

    if new_episodes:
        data["episodes"].extend(new_episodes)
        data["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        save_episodes(data)
        print(f"\nAdded {len(new_episodes)} new episode(s) to {EPISODES_JSON}")
    else:
        print("\nNo new episodes found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
