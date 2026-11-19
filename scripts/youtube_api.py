"""Full Generation AI episodes from the YouTube Data API v3.

Used whenever YOUTUBE_API_KEY is set (the GitHub workflow). YouTube serves its
watch pages to GitHub's servers without video details (Nov. 19, 2026), so the
page reader in youtube_playlist.py is only a local fallback. Two calls a run in
practice: playlistItems.list (1 unit per 50 videos) and videos.list (1 unit per
50 videos), from a 10,000-unit daily quota.

The key goes only in the request URL and is never printed: errors are re-raised
without the URL.
"""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from youtube_playlist import MIN_SECONDS, PlaylistError, arizona_date, first_paragraph

API = "https://www.googleapis.com/youtube/v3/"
MAX_PAGES = 40  # 50 videos a page
RETRY_WAITS = (10, 30, 60)


def _call(endpoint, params, key, fetch=None):
    query = urllib.parse.urlencode({**params, "key": key})
    if fetch:
        return json.loads(fetch(endpoint, params))
    for attempt, wait in enumerate((*RETRY_WAITS, None)):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{API}{endpoint}?{query}", headers={"Accept": "application/json"}), timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            reason = ""
            try:
                reason = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")[:200]
            except Exception:
                pass
            if wait is not None and (e.code == 429 or e.code >= 500):
                print(f"  YouTube API answered {e.code}; waiting {wait}s before retry {attempt + 1}...")
                time.sleep(wait)
                continue
            raise PlaylistError(f"YouTube API {endpoint} failed ({e.code}) {reason}".strip()) from None
        except (urllib.error.URLError, TimeoutError):
            if wait is None:
                raise PlaylistError(f"YouTube API {endpoint} could not be reached") from None
            time.sleep(wait)


def duration_seconds(iso):
    """ISO 8601 duration (PT26M10S, PT1H2M) to seconds."""
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m or iso in ("P", "PT"):
        raise PlaylistError(f"Unreadable video duration {iso!r}")
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def playlist_video_ids(playlist_id, key, fetch=None):
    ids, token, pages = [], None, 0
    while True:
        params = {"part": "contentDetails", "playlistId": playlist_id, "maxResults": 50}
        if token:
            params["pageToken"] = token
        data = _call("playlistItems", params, key, fetch)
        for item in data.get("items", []):
            vid = item.get("contentDetails", {}).get("videoId")
            if vid and vid not in ids:
                ids.append(vid)
        token = data.get("nextPageToken")
        pages += 1
        if not token:
            break
        if pages >= MAX_PAGES:
            raise PlaylistError("Playlist is unexpectedly long; review before importing")
    if not ids:
        raise PlaylistError("The YouTube API returned no videos for the playlist")
    return ids


def full_episodes(playlist_id, key, fetch=None):
    """Full episodes (24 minutes or longer), with Arizona date and description, in playlist order."""
    ids = playlist_video_ids(playlist_id, key, fetch)
    details = {}
    for start in range(0, len(ids), 50):
        data = _call("videos", {"part": "contentDetails,snippet", "id": ",".join(ids[start:start + 50]), "maxResults": 50}, key, fetch)
        for v in data.get("items", []):
            details[v["id"]] = v
    episodes = []
    for vid in ids:
        v = details.get(vid)
        if not v:
            continue  # Private or deleted: YouTube returns no details, and the website can't show it.
        seconds = duration_seconds(v.get("contentDetails", {}).get("duration"))
        if seconds < MIN_SECONDS:
            continue
        snippet = v.get("snippet", {})
        published = snippet.get("publishedAt")
        if not published or not snippet.get("title"):
            raise PlaylistError(f"Video {vid} is missing its title or publish time")
        date = arizona_date(published.replace("Z", "+00:00"))
        formatted = re.sub(r" 0(\d)", r" \1", datetime.strptime(date, "%Y-%m-%d").strftime("%B %d, %Y"))
        episodes.append({"youtubeId": vid, "title": snippet["title"].strip(), "seconds": seconds, "published": published,
                         "date": date, "dateFormatted": formatted, "description": first_paragraph(snippet.get("description", ""))})
    return episodes
