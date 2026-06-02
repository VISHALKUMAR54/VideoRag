import asyncio
import os
import re
import subprocess
import tempfile
import time
import json
from typing import Callable, Any

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from youtube_transcript_api._errors import TranscriptsDisabled
import instaloader
from groq import Groq

from config import YOUTUBE_API_KEY, GROQ_API_KEY


# extract youtube video id from url
def _extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/watch\?v=|\/watch\?.+&v=)([^#\&\?]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract video ID from YouTube URL: {url}")


# retrieve transcript using youtube api client library
def _get_youtube_transcript(yt_id: str) -> str:
    try:
        transcript_list = YouTubeTranscriptApi().fetch(yt_id)
        return " ".join([item.text for item in transcript_list])
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        raise RuntimeError(f"YouTube transcript is disabled or not found for {yt_id}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch YouTube transcript: {e}")


# parses ISO duration formats
def _parse_iso_duration(duration: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not m:
        return 0
    h, mn, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mn * 60 + s


# retrieve youtube video statistics and metadata
def _get_youtube_metadata(yt_id: str) -> dict:
    if not YOUTUBE_API_KEY:
        print("[YouTube] WARNING: YOUTUBE_API_KEY not set in environment. Returning fallback/zeros.")
        return {
            "title": f"YouTube Video ({yt_id})",
            "creator": "unknown",
            "follower_count": None,
            "views": 0,
            "likes": 0,
            "comments": 0,
            "engagement_rate": 0.0,
            "upload_date": None,
            "duration_seconds": 0,
            "hashtags": [],
        }
    
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        req = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=yt_id
        )
        res = req.execute()
        
        if not res.get("items"):
            raise ValueError(f"No video items returned for ID: {yt_id}")
            
        item = res["items"][0]
        snip = item["snippet"]
        stats = item["statistics"]
        
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        
        engagement_rate = 0.0
        if views > 0:
            engagement_rate = round((likes + comments) / views * 100, 2)
            
        return {
            "title":           snip["title"],
            "creator":         snip["channelTitle"],
            "follower_count":  None,
            "views":           views,
            "likes":           likes,
            "comments":        comments,
            "engagement_rate": engagement_rate,
            "upload_date":     snip["publishedAt"][:10],
            "duration_seconds": _parse_iso_duration(item["contentDetails"]["duration"]),
            "hashtags":        snip.get("tags", []),
        }
    except Exception as e:
        print(f"[YouTube] Error fetching metadata: {e}")
        raise RuntimeError(f"Failed to fetch YouTube metadata: {e}")


# run youtube ingestion pipeline
async def ingest_youtube(url: str, video_id: str = "A") -> dict:
    print(f"\n[YouTube] Ingesting Video {video_id}: {url}")
    yt_id = _extract_video_id(url)
    loop  = asyncio.get_event_loop()
    _t0   = time.perf_counter()

    transcript, metadata = await asyncio.gather(
        loop.run_in_executor(None, _get_youtube_transcript, yt_id),
        loop.run_in_executor(None, _get_youtube_metadata,   yt_id),
    )
    print(f"[YouTube] Video {video_id} done ✓  [total: {time.perf_counter()-_t0:.2f}s]")
    return {"video_id": video_id, "url": url, "transcript": transcript, **metadata}


# extract shortcode from instagram url
def _extract_shortcode(url: str) -> str:
    m = re.search(r"/(?:reel|p|tv)/([A-Za-z0-9_-]+)", url)
    if not m:
        raise ValueError(f"Cannot extract Instagram shortcode from: {url}")
    return m.group(1)


# download instagram reel video using yt-dlp
def _download_via_ytdlp(url: str, tmpdir: str) -> str:
    import sys
    ytdlp_bin = "yt-dlp"
    venv_bin_dir = os.path.dirname(sys.executable)
    local_ytdlp = os.path.join(venv_bin_dir, "yt-dlp")
    if os.path.exists(local_ytdlp):
        ytdlp_bin = local_ytdlp
        
    out_path = os.path.join(tmpdir, "reel.mp4")
    browsers = [None, 'chrome', 'firefox', 'brave', 'edge', 'safari', 'opera']
    last_err = ""
    
    for browser in browsers:
        cmd = [ytdlp_bin, "-o", out_path, "--quiet", "--no-playlist"]
        if browser:
            cmd.extend(["--cookies-from-browser", browser])
        cmd.append(url)
        
        print(f"  [Instagram] Downloading reel via yt-dlp (browser={browser or 'standard'}) ...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if not os.path.exists(out_path):
                files = [f for f in os.listdir(tmpdir) if f.startswith("reel")]
                if not files:
                    continue
                out_path = os.path.join(tmpdir, files[0])
            print(f"  [Instagram] yt-dlp: got {os.path.basename(out_path)} ({os.path.getsize(out_path)/1e6:.1f} MB)")
            return out_path
        else:
            last_err = result.stderr or result.stdout
            
    raise RuntimeError(f"All yt-dlp download attempts failed. Last error: {last_err}")


# retrieve instagram video metadata using yt-dlp fallback
def _get_instagram_metadata_via_ytdlp(url: str) -> dict:
    import sys
    ytdlp_bin = "yt-dlp"
    venv_bin_dir = os.path.dirname(sys.executable)
    local_ytdlp = os.path.join(venv_bin_dir, "yt-dlp")
    if os.path.exists(local_ytdlp):
        ytdlp_bin = local_ytdlp
        
    browsers = [None, 'chrome', 'firefox', 'brave', 'edge', 'safari', 'opera']
    last_err = ""
    
    for browser in browsers:
        cmd = [ytdlp_bin, "--dump-json", "--no-playlist"]
        if browser:
            cmd.extend(["--cookies-from-browser", browser])
        cmd.append(url)
        
        print(f"  [Instagram] Fetching metadata via yt-dlp (browser={browser or 'standard'}) ...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                info = json.loads(result.stdout)
                creator = info.get("uploader") or info.get("channel") or "unknown"
                if creator != "unknown" and not creator.startswith("@"):
                    creator = f"@{creator}"
                
                views = int(info.get("view_count") or 0)
                likes = int(info.get("like_count") or 0)
                comments = int(info.get("comment_count") or 0)
                
                engagement_rate = 0.0
                if views > 0:
                    engagement_rate = round((likes + comments) / views * 100, 2)
                    
                raw_date = info.get("upload_date") or ""
                upload_date = None
                if len(raw_date) == 8:
                    upload_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
                    
                duration = int(info.get("duration") or 0)
                
                desc = info.get("description") or info.get("title") or ""
                hashtags = re.findall(r"#(\w+)", desc)
                
                thumb_url = info.get("thumbnail") or ""
                if not thumb_url:
                    thumbs = info.get("thumbnails") or []
                    if thumbs:
                        thumb_url = thumbs[-1].get("url", "")

                metadata = {
                    "platform":        "instagram",
                    "title":           (info.get("title") or "")[:80] or f"Reel by {creator}",
                    "creator":         creator,
                    "follower_count":  None,
                    "views":           views,
                    "likes":           likes,
                    "comments":        comments,
                    "engagement_rate": engagement_rate,
                    "upload_date":     upload_date,
                    "duration_seconds": duration,
                    "hashtags":        hashtags,
                    "thumbnail_url":   thumb_url,
                }
                print(f"  [Instagram] Thumbnail: {thumb_url[:80] if thumb_url else 'not found'}")
                print(f"  [Instagram] Real metadata extracted via yt-dlp ({browser or 'standard'}): views={views:,} | likes={likes:,} | engagement={engagement_rate}%")
                return metadata
            except Exception as e:
                print(f"  [Instagram] Failed to parse yt-dlp JSON: {e}")
        else:
            last_err = result.stderr or result.stdout
            
    raise RuntimeError(f"All yt-dlp metadata extraction attempts failed. Last error: {last_err}")


# transcribes audio using Groq Whisper API
def _transcribe_with_whisper(mp4_path: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    print(f"  [Instagram] Groq Whisper: transcribing {os.path.basename(mp4_path)} ...")
    _t0 = time.perf_counter()
    with open(mp4_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            response_format="text",
        )
    text = result if isinstance(result, str) else result.text
    print(f"  [Instagram] Groq Whisper: {len(text)} chars transcribed  [{time.perf_counter()-_t0:.2f}s]")
    return text


# runs instagram ingestion pipeline synchronously in thread pool
def _ingest_instagram_sync(url: str, video_id: str) -> dict:
    shortcode  = _extract_shortcode(url)
    post       = None
    metadata   = {}

    _t_total = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmpdir:
        _t_meta_fetch = time.perf_counter()
        L = instaloader.Instaloader(
            download_pictures=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            quiet=True,
        )
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            print(f"  [Instagram] ✓ Metadata object fetched from instaloader in [{time.perf_counter()-_t_meta_fetch:.2f}s]")
        except Exception as e_meta:
            print(f"  [Instagram] ✗ Metadata fetch via instaloader failed: {e_meta}")
            print(f"  [Instagram] Falling back to real metadata extraction via yt-dlp ...")
            try:
                metadata = _get_instagram_metadata_via_ytdlp(url)
            except Exception as e_ytdlp_meta:
                print(f"  [Instagram] ✗ yt-dlp metadata extraction failed: {e_ytdlp_meta}")

        mp4_path = None
        if post:
            _t_instaloader_dl = time.perf_counter()
            try:
                print(f"  [Instagram] instaloader: downloading shortcode={shortcode} ...")
                L.download_post(post, target=tmpdir)
                mp4_files = [f for f in os.listdir(tmpdir) if f.endswith(".mp4")]
                if mp4_files:
                    mp4_path = os.path.join(tmpdir, mp4_files[0])
                    print(f"  [Instagram] ✓ Download (instaloader): [{time.perf_counter()-_t_instaloader_dl:.2f}s]")
            except Exception as e_dl:
                print(f"  [Instagram] ✗ instaloader download failed: {e_dl}")

        if not mp4_path:
            print(f"  [Instagram] → yt-dlp fallback for video download ...")
            _t_ytdlp = time.perf_counter()
            try:
                mp4_path = _download_via_ytdlp(url, tmpdir)
                print(f"  [Instagram] ✓ Download (yt-dlp) successful in [{time.perf_counter()-_t_ytdlp:.2f}s]")
            except Exception as e_ytdlp:
                print(f"  [Instagram] ✗ yt-dlp download failed: {e_ytdlp}")
                raise RuntimeError(f"Failed to download video using both instaloader and yt-dlp: {e_ytdlp}")

        _t_whisper = time.perf_counter()
        transcript = _transcribe_with_whisper(mp4_path)
        print(f"  [Instagram] Transcription phase: [{time.perf_counter()-_t_whisper:.2f}s]")
        print(f"  [Instagram] Pipeline total: [{time.perf_counter()-_t_total:.2f}s]")

        if post:
            _t_meta_extract = time.perf_counter()
            views    = post.video_view_count or 0
            likes    = post.likes            or 0
            comments = post.comments         or 0
            engagement_rate = round((likes + comments) / views * 100, 2) if views else 0.0

            _t_fol = time.perf_counter()
            try:
                follower_count = post.owner_profile.followers
                print(f"  [Instagram] ✓ Follower count fetched [{time.perf_counter()-_t_fol:.2f}s]")
            except Exception as e_fol:
                follower_count = None
                print(f"  [Instagram] Note: follower count unavailable ({e_fol})")

            metadata = {
                "platform":        "instagram",
                "title":           (post.caption or "")[:80] or f"Reel by @{post.owner_username}",
                "creator":         f"@{post.owner_username}",
                "follower_count":  follower_count,
                "views":           views,
                "likes":           likes,
                "comments":        comments,
                "engagement_rate": engagement_rate,
                "upload_date":     str(post.date.date()),
                "duration_seconds": int(post.video_duration or 0),
                "hashtags":        list(post.caption_hashtags),
                "thumbnail_url":   getattr(post, "url", "") or "",
            }
            print(
                f"  [Instagram] @{post.owner_username} | "
                f"views={views:,} | likes={likes:,} | engagement={engagement_rate}% | "
                f"followers={follower_count}"
            )
            print(f"  [Instagram] Metadata extraction: [{time.perf_counter()-_t_meta_extract:.2f}s]")

    return {
        "video_id":   video_id,
        "url":        url,
        "transcript": transcript,
        **metadata,
    }


# run instagram ingestion pipeline
async def ingest_instagram(url: str, video_id: str = "B") -> dict:
    print(f"\n[Instagram] Ingesting Video {video_id}: {url}")
    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _ingest_instagram_sync, url, video_id)
    print(f"[Instagram] Video {video_id} done ✓")
    return result


# runs youtube + instagram ingestion concurrently
async def run_ingestion_pipeline(
    yt_url:   str,
    ig_url:   str,
    job_id:   str,
    on_progress=None,
) -> tuple[dict, dict]:
    async def _progress(pct: int, stage: str):
        print(f"  [Pipeline] {pct}% — {stage}")
        if on_progress:
            await on_progress(job_id, pct, stage)

    await _progress(10, "Fetching YouTube transcript + Instagram metadata...")

    has_yt = bool(yt_url and yt_url.strip())
    has_ig = bool(ig_url and ig_url.strip())

    tasks = []

    if has_yt:
        tasks.append(ingest_youtube(yt_url, video_id="A"))
    else:
        async def empty_yt():
            return {
                "video_id": "A",
                "platform": "youtube",
                "url": "",
                "title": "Not Provided",
                "creator": "unknown",
                "follower_count": None,
                "views": 0,
                "likes": 0,
                "comments": 0,
                "engagement_rate": 0.0,
                "upload_date": "",
                "duration_seconds": 0,
                "hashtags": [],
                "transcript": "",
            }
        tasks.append(empty_yt())

    if has_ig:
        tasks.append(ingest_instagram(ig_url, video_id="B"))
    else:
        async def empty_ig():
            return {
                "video_id": "B",
                "platform": "instagram",
                "url": "",
                "title": "Not Provided",
                "creator": "unknown",
                "follower_count": None,
                "views": 0,
                "likes": 0,
                "comments": 0,
                "engagement_rate": 0.0,
                "upload_date": "",
                "duration_seconds": 0,
                "hashtags": [],
                "transcript": "",
            }
        tasks.append(empty_ig())

    yt_data, ig_data = await asyncio.gather(*tasks)
    await _progress(45, "All media fetched and transcribed.")
    return yt_data, ig_data
