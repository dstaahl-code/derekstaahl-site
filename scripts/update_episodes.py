#!/usr/bin/env python3
"""
Fetch new Generation AI episodes from the AZFamily YouTube playlist RSS feed,
optionally scrape azfamily.com for the matching article link, and write new
episodes to Airtable.

Falls back to data/episodes.json if AIRTABLE_API_KEY and AIRTABLE_BASE_ID
are not set (for local testing without credentials).

Uses only Python standard library -- no pip install needed.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
EPISODES_JSON = os.path.join(PROJECT_ROOT, "data", "episodes.json")

# Generation AI playlist on the AZFamily YouTube channel
PLAYLIST_ID = "PLJQ20huef_NwQoBRT-QSNP3vl9hoV4OWy"
YOUTUBE_RSS = f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"

AZFAMILY_TECH_URL = "https://www.azfamily.com/news/technology/"

AIRTABLE_BASE_URL = "https://api.airtable.com/v0"
AIRTABLE_TABLE = "YouTube%20Videos"

# Namespaces used in the YouTube RSS feed
YT_NS = "http://www.youtube.com/xml/schemas/2015"
MEDIA_NS = "http://search.yahoo.com/mrss/"
ATOM_NS = "http://www.w3.org/2005/Atom"

GENAI_PATTERN = re.compile(r"generation\s+ai", re.IGNORECASE)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_url(url, retries=3):
    """Fetch a URL and return the response body as a string, with retries."""
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries:
                wait = 2 ** attempt
                print(f"  Attempt {attempt} failed ({e}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


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
            if GENAI_PATTERN.search(text) or GENAI_PATTERN.search(href):
                self.links.append({"href": href, "text": text})


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

    title_words = set(re.findall(r"\w+", episode_title.lower()))
    best_match = ""
    best_score = 0

    for link in azfamily_links:
        link_words = set(re.findall(r"\w+", (link["text"] + " " + link["href"]).lower()))
        overlap = len(title_words & link_words)
        if overlap > best_score:
            best_score = overlap
            best_match = link["href"]

    if best_score >= 3:
        if best_match.startswith("/"):
            best_match = "https://www.azfamily.com" + best_match
        return best_match

    return ""


# =============================================================================
# Airtable
# =============================================================================

def airtable_request(method, url, api_key, body=None):
    """Make an Airtable API request and return parsed JSON."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": USER_AGENT,
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Airtable API error {e.code}: {body_text}") from e


def get_airtable_episodes(base_id, api_key):
    """Return (existing_video_ids dict, max_episode_number) from Airtable."""
    existing = {}  # youtube_id -> record_id
    max_ep_num = 0
    offset = None

    while True:
        params = [
            ("fields[]", "YouTube ID"),
            ("fields[]", "Episode Number"),
        ]
        if offset:
            params.append(("offset", offset))

        url = (
            f"{AIRTABLE_BASE_URL}/{base_id}/{AIRTABLE_TABLE}"
            f"?{urllib.parse.urlencode(params)}"
        )
        result = airtable_request("GET", url, api_key)

        for record in result.get("records", []):
            fields = record.get("fields", {})
            yt_id = fields.get("YouTube ID", "")
            ep_num = fields.get("Episode Number") or 0
            if yt_id:
                existing[yt_id] = record["id"]
            if ep_num > max_ep_num:
                max_ep_num = int(ep_num)

        offset = result.get("offset")
        if not offset:
            break

    return existing, max_ep_num


def create_airtable_episode(base_id, api_key, ep, ep_number, azfamily_url):
    """POST a new episode record to Airtable. Returns the new record ID."""
    thumbnail_url = f"https://img.youtube.com/vi/{ep['youtubeId']}/maxresdefault.jpg"

    fields = {
        "Title": ep["title"],
        "Episode Number": ep_number,
        "YouTube ID": ep["youtubeId"],
        "Thumbnail URL": thumbnail_url,
        "Air Date": ep["date"],
        "Show on Website": True,
    }
    if ep["description"]:
        fields["Description"] = ep["description"]
    if azfamily_url:
        fields["AZFamily URL"] = azfamily_url

    url = f"{AIRTABLE_BASE_URL}/{base_id}/{AIRTABLE_TABLE}"
    result = airtable_request("POST", url, api_key, body={"fields": fields})
    return result.get("id")


def write_episodes_to_airtable(episodes_with_urls, base_id, api_key):
    """Write new episodes to Airtable. Returns count of created records."""
    print("Querying Airtable for existing episodes...")
    existing_ids, max_ep_num = get_airtable_episodes(base_id, api_key)
    print(
        f"Found {len(existing_ids)} existing episode(s) in Airtable "
        f"(max episode #{max_ep_num})."
    )

    created = 0
    next_ep_num = max_ep_num

    for ep, azfamily_url in episodes_with_urls:
        if ep["youtubeId"] in existing_ids:
            print(f"  Skipping (already in Airtable): {ep['title']}")
            continue

        next_ep_num += 1
        record_id = create_airtable_episode(base_id, api_key, ep, next_ep_num, azfamily_url)
        print(f"  Created record {record_id}: {ep['title']} (Episode #{next_ep_num})")
        if azfamily_url:
            print(f"    AZFamily: {azfamily_url}")
        created += 1

    return created


# =============================================================================
# JSON fallback (used when Airtable env vars are not set)
# =============================================================================

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


def write_episodes_to_json(episodes_with_urls, existing_data):
    """Append new episodes to data/episodes.json. Returns count added."""
    existing_ids = {ep["youtubeId"] for ep in existing_data["episodes"]}
    added = 0

    for ep, azfamily_url in episodes_with_urls:
        if ep["youtubeId"] in existing_ids:
            print(f"  Skipping (already exists): {ep['title']}")
            continue

        new_ep = {
            "number": len(existing_data["episodes"]) + added + 1,
            "title": ep["title"],
            "guest": "",
            "date": ep["date"],
            "dateFormatted": ep["dateFormatted"],
            "description": ep["description"],
            "youtubeId": ep["youtubeId"],
            "azfamilyUrl": azfamily_url,
        }
        existing_data["episodes"].append(new_ep)
        print(f"  New episode: {ep['title']}")
        if azfamily_url:
            print(f"    AZFamily article: {azfamily_url}")
        else:
            print("    No AZFamily article found (can be added manually)")
        added += 1

    return added


def main():
    airtable_api_key = os.environ.get("AIRTABLE_API_KEY")
    airtable_base_id = os.environ.get("AIRTABLE_BASE_ID")
    use_airtable = bool(airtable_api_key and airtable_base_id)

    if use_airtable:
        print("Airtable credentials found -- writing to Airtable.")
    else:
        print("No Airtable credentials -- falling back to data/episodes.json.")

    print(f"Fetching YouTube RSS feed for playlist {PLAYLIST_ID}...")
    try:
        yt_episodes = parse_youtube_rss()
    except Exception as e:
        print(f"Error: Could not fetch YouTube RSS feed after retries: {e}", file=sys.stderr)
        print("Exiting gracefully -- will retry on next scheduled run.")
        return 0
    print(f"Found {len(yt_episodes)} episode(s) in playlist feed.")

    # Scrape AZFamily (best-effort)
    print("Scraping azfamily.com for article links...")
    azfamily_links = scrape_azfamily_links()
    print(f"Found {len(azfamily_links)} Generation AI link(s) on azfamily.com.")

    # Pair each episode with its matched AZFamily URL
    episodes_with_urls = [
        (ep, match_article_url(ep["title"], azfamily_links))
        for ep in yt_episodes
    ]

    if use_airtable:
        try:
            created = write_episodes_to_airtable(episodes_with_urls, airtable_base_id, airtable_api_key)
            if created:
                print(f"\nCreated {created} new episode(s) in Airtable.")
            else:
                print("\nNo new episodes to add.")
        except Exception as e:
            print(f"Error writing to Airtable: {e}", file=sys.stderr)
            return 1
    else:
        data = load_episodes()
        added = write_episodes_to_json(episodes_with_urls, data)
        if added:
            data["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            save_episodes(data)
            print(f"\nAdded {added} new episode(s) to {EPISODES_JSON}")
        else:
            print("\nNo new episodes found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
