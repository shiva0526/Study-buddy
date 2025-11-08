# backend/app/services/youtube.py
import os
import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)
YT_API_KEY = os.getenv("YT_API_KEY")  # put your key in .env

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = "https://www.youtube.com/watch?v={videoId}"

def search_videos(query: str, max_results: int = 5) -> List[Dict]:
    """
    Simple search using YouTube Data API v3. Returns list of dicts:
    [{videoId, title, description, url}]
    """
    if not YT_API_KEY:
        logger.warning("YT_API_KEY not set — returning empty results")
        return []
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YT_API_KEY,
    }
    try:
        r = requests.get(SEARCH_URL, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        results = []
        for it in data.get("items", []):
            vid = it["id"]["videoId"]
            snip = it["snippet"]
            results.append({
                "videoId": vid,
                "title": snip.get("title"),
                "description": snip.get("description"),
                "url": VIDEO_URL.format(videoId=vid)
            })
        return results
    except Exception as e:
        logger.exception("YouTube API search failed: %s", e)
        return []
