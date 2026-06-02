import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter(tags=["thumbnail"])

# user-agent and headers to bypass CDN bot detection
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.instagram.com/",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


# proxies instagram cdn thumbnail to avoid cross-origin blocking
@router.get("/thumbnail")
async def proxy_thumbnail(url: str = Query(..., description="CDN thumbnail URL to proxy")) -> Response:
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Only https:// URLs are allowed.")

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            upstream = await client.get(url, headers=_HEADERS)

        if upstream.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Upstream returned {upstream.status_code}"
            )

        content_type = upstream.headers.get("content-type", "image/jpeg")

        return Response(
            content=upstream.content,
            media_type=content_type,
            headers={
                "Cross-Origin-Resource-Policy": "cross-origin",
                "Cache-Control": "public, max-age=3600",
            },
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream thumbnail request timed out.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch thumbnail: {e}")
