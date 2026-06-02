from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

# text splitter instance
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
)

# keys to copy from video metadata to each chunk payload
_METADATA_KEYS = [
    "video_id",
    "platform",
    "url",
    "title",
    "creator",
    "follower_count",
    "views",
    "likes",
    "comments",
    "engagement_rate",
    "upload_date",
    "duration_seconds",
    "hashtags",
]


# splits transcript into overlapping chunks and attaches metadata
def chunk_video(video_data: dict) -> list[dict]:
    transcript = video_data.get("transcript", "")
    if not transcript:
        print(f"  [Chunker] WARNING: empty transcript for video_id={video_data.get('video_id')}")
        return []

    chunk_metadata = {k: video_data.get(k) for k in _METADATA_KEYS}
    raw_chunks = _splitter.split_text(transcript)

    print(
        f"  [Chunker] video_id={video_data.get('video_id')} | "
        f"{len(transcript)} chars → {len(raw_chunks)} chunks "
        f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )

    return [
        {
            "text":        chunk,
            "chunk_index": i,
            **chunk_metadata,
        }
        for i, chunk in enumerate(raw_chunks)
    ]
