"""Read the full Generation AI playlist from YouTube's own pages.

The playlist RSS feed returns only the first 15 videos in playlist order, and
this playlist runs oldest to newest, so every episode after the 15th was
invisible to the grabber from about March 2026. The playlist page lists every
video with its run time; each new video's watch page gives its publish date and
description. Anything unreadable raises, so a changed page fails the run
instead of quietly reporting "no new episodes".

Standard library only.
"""

import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

MIN_SECONDS = 24 * 60  # Full episodes run about 26 minutes; segments are shorter.
ARIZONA = timezone(timedelta(hours=-7))  # No daylight saving time.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_PAGES = 20  # 100 videos a page.
# YouTube answers 429 when a runner opens many pages quickly (Nov. 19 backfill).
RETRY_WAITS = (10, 30, 60)
WATCH_PAUSE = 3  # seconds between watch-page lookups


class PlaylistError(Exception):
    pass


def _get(url, data=None, fetch=None):
    if fetch:
        return fetch(url, data)
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    for attempt, wait in enumerate((*RETRY_WAITS, None)):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST" if body else "GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if wait is None or (e.code != 429 and e.code < 500):
                raise
            print(f"  YouTube answered {e.code}; waiting {wait}s before retry {attempt + 1}...")
            time.sleep(wait)
        except urllib.error.URLError:
            if wait is None:
                raise
            time.sleep(wait)


def _json_after(html, marker):
    """Parse the JSON object assigned right after `marker` in a page's script."""
    start = html.find(marker)
    if start < 0:
        raise PlaylistError(f"YouTube page is missing {marker.strip()}")
    start = html.index("{", start)
    try:
        value, _ = json.JSONDecoder().raw_decode(html, start)
    except ValueError as e:
        raise PlaylistError(f"YouTube page data could not be read: {e}")
    return value


def _walk(node):
    stack = [node]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            yield item
            stack.extend(reversed(list(item.values())))
        elif isinstance(item, list):
            stack.extend(reversed(item))


def _seconds(text):
    parts = (text or "").strip().split(":")
    if not parts or not all(p.isdigit() for p in parts) or len(parts) > 3:
        return None
    total = 0
    for p in parts:
        total = total * 60 + int(p)
    return total


def _videos_in(data):
    """Videos in page order, from either of YouTube's two playlist layouts."""
    videos = []
    for node in _walk(data):
        if "playlistVideoRenderer" in node:
            v = node["playlistVideoRenderer"]
            title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", [])) or v.get("title", {}).get("simpleText", "")
            seconds = int(v["lengthSeconds"]) if str(v.get("lengthSeconds", "")).isdigit() else None
            videos.append({"youtubeId": v.get("videoId"), "title": title.strip(), "seconds": seconds})
        elif "lockupViewModel" in node:
            v = node["lockupViewModel"]
            badge = None
            for inner in _walk(v.get("contentImage", {})):
                if "thumbnailBadgeViewModel" in inner:
                    badge = inner["thumbnailBadgeViewModel"].get("text")
                    break
            title = v.get("metadata", {}).get("lockupMetadataViewModel", {}).get("title", {}).get("content", "")
            videos.append({"youtubeId": v.get("contentId"), "title": title.strip(), "seconds": _seconds(badge)})
    return videos


def _continuation(data):
    """The "load more videos" token: a continuation item in the same list as the
    videos. Other continuations on the page (later page sections) are ignored."""
    def is_video(item):
        return isinstance(item, dict) and ("playlistVideoRenderer" in item or "lockupViewModel" in item)
    stack = [data]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            if any(is_video(x) for x in item):
                for x in item:
                    if isinstance(x, dict) and not is_video(x):
                        for inner in _walk(x):
                            command = inner.get("continuationCommand")
                            if isinstance(command, dict) and command.get("token"):
                                return command["token"]
            stack.extend(item)
    return None


def playlist_videos(playlist_id, fetch=None):
    """Every video in the playlist, in playlist order, with run times."""
    html = _get(f"https://www.youtube.com/playlist?list={playlist_id}", fetch=fetch)
    data = _json_after(html, "var ytInitialData =")
    videos = _videos_in(data)
    config = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
    token = _continuation(data)
    pages = 1
    while token:
        if not config:
            raise PlaylistError("YouTube page is missing its client version; cannot load more videos")
        if pages >= MAX_PAGES:
            raise PlaylistError("Playlist is unexpectedly long; review before importing")
        more = json.loads(_get("https://www.youtube.com/youtubei/v1/browse?prettyPrint=false",
                               {"context": {"client": {"clientName": "WEB", "clientVersion": config.group(1), "hl": "en"}}, "continuation": token},
                               fetch=fetch))
        found = _videos_in(more)
        if not found:
            raise PlaylistError("YouTube returned an empty continuation page")
        videos.extend(found)
        token = _continuation(more)
        pages += 1
    if not videos:
        raise PlaylistError("No videos found on the playlist page; YouTube's layout may have changed")
    for v in videos:
        if not v["youtubeId"] or not re.fullmatch(r"[A-Za-z0-9_-]{11}", v["youtubeId"]) or not v["title"]:
            raise PlaylistError("A playlist video is missing its ID or title")
        if v["seconds"] is None:
            raise PlaylistError(f"Run time missing for {v['youtubeId']}; cannot tell an episode from a segment")
    ids = [v["youtubeId"] for v in videos]
    if len(ids) != len(set(ids)):
        # Keep the first occurrence; YouTube can repeat an item across pages.
        seen, unique = set(), []
        for v in videos:
            if v["youtubeId"] not in seen:
                seen.add(v["youtubeId"])
                unique.append(v)
        videos = unique
    return videos


def full_episodes(playlist_id, fetch=None):
    return [v for v in playlist_videos(playlist_id, fetch=fetch) if v["seconds"] >= MIN_SECONDS]


def first_paragraph(text):
    """The description's first paragraph, stopping at the first link line (as before)."""
    paragraphs = re.split(r"\n\s*\n", (text or "").strip())
    lines = []
    for line in (paragraphs[0] if paragraphs else "").split("\n"):
        if re.match(r"https?://", line.strip()):
            break
        lines.append(line.strip())
    return " ".join(l for l in lines if l)


def arizona_date(published):
    """YYYY-MM-DD in Arizona for an ISO timestamp with an offset."""
    try:
        moment = datetime.fromisoformat(published)
    except (TypeError, ValueError):
        raise PlaylistError(f"Unreadable publish time {published!r}")
    if moment.tzinfo is None:
        raise PlaylistError(f"Publish time without a time zone: {published!r}")
    return moment.astimezone(ARIZONA).strftime("%Y-%m-%d")


_last_watch = [0.0]


def video_details(video, fetch=None):
    """Adds date, dateFormatted, description and published to a playlist video."""
    if not fetch:
        gap = WATCH_PAUSE - (time.monotonic() - _last_watch[0])
        if gap > 0:
            time.sleep(gap)
        _last_watch[0] = time.monotonic()
    html = _get(f"https://www.youtube.com/watch?v={video['youtubeId']}", fetch=fetch)
    player = _json_after(html, "var ytInitialPlayerResponse =")
    details = player.get("videoDetails", {})
    micro = player.get("microformat", {}).get("playerMicroformatRenderer", {})
    published = micro.get("publishDate") or micro.get("uploadDate")
    if details.get("videoId") != video["youtubeId"] or not published:
        raise PlaylistError(f"Watch page for {video['youtubeId']} is missing its details")
    date = arizona_date(published)
    formatted = re.sub(r" 0(\d)", r" \1", datetime.strptime(date, "%Y-%m-%d").strftime("%B %d, %Y"))
    return {**video, "title": (details.get("title") or video["title"]).strip(), "published": published,
            "date": date, "dateFormatted": formatted, "description": first_paragraph(details.get("shortDescription", ""))}
