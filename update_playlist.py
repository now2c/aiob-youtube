#!/usr/bin/env python3
"""
Fetch YouTube playlist RSS feed and update index.html with latest episodes.
"""

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

PLAYLIST_ID = "PLQAcFocMCkSan2LR8WPs-BhUGdQEk0dfi"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"
HTML_FILE = "index.html"


def fetch_rss():
    """Fetch the YouTube playlist RSS feed."""
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_rss(xml_content):
    """Parse RSS feed and extract video information."""
    root = ET.fromstring(xml_content)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "media": "http://search.yahoo.com/mrss/",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }

    episodes = []
    for entry in root.findall("atom:entry", ns):
        video_id = entry.find("yt:videoId", ns).text
        title = entry.find("atom:title", ns).text
        published = entry.find("atom:published", ns).text
        views = entry.find("media:group/media:community/media:statistics", ns).get(
            "views", "0"
        )

        # Parse date
        date_obj = datetime.fromisoformat(published.replace("Z", "+00:00"))
        date_str = date_obj.strftime("%Y.%m.%d")

        episodes.append(
            {
                "vid": video_id,
                "title": title,
                "date": date_str,
                "views": views,
                "published": date_obj,
            }
        )

    # Sort by published date (newest first)
    episodes.sort(key=lambda x: x["published"], reverse=True)

    # Assign episode numbers
    for i, ep in enumerate(episodes, 1):
        ep["ep"] = len(episodes) - i + 1

    return episodes


def get_duration(video_id):
    """Try to get video duration from oEmbed or return placeholder."""
    # YouTube oEmbed doesn't provide duration, so we'll use a placeholder
    # The duration will be updated when someone manually checks
    return "--:--"


def generate_episodes_js(episodes):
    """Generate the JavaScript episodes array."""
    items = []
    for ep in episodes:
        item = {
            "ep": ep["ep"],
            "vid": ep["vid"],
            "dur": get_duration(ep["vid"]),
            "title": ep["title"],
            "date": ep["date"],
            "views": ep["views"],
        }
        items.append(item)
    return json.dumps(items, ensure_ascii=False, indent=2)


def update_html(episodes_js):
    """Update the episodes array in index.html."""
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Find and replace the episodes array
    pattern = r"const episodes = \[[\s\S]*?\];"
    new_array = f"const episodes = {episodes_js};"

    if re.search(pattern, content):
        content = re.sub(pattern, new_array, content)
        with open(HTML_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    else:
        print("Could not find episodes array in HTML", file=sys.stderr)
        return False


def main():
    print("Fetching YouTube playlist RSS feed...")
    xml_content = fetch_rss()

    print("Parsing RSS feed...")
    episodes = parse_rss(xml_content)
    print(f"Found {len(episodes)} videos")

    print("Generating JavaScript...")
    episodes_js = generate_episodes_js(episodes)

    print("Updating HTML...")
    if update_html(episodes_js):
        print("Successfully updated index.html")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
