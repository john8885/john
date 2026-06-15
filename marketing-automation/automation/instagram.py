"""Instagram 자동 포스팅 (피드 이미지, 릴스)"""
import logging
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

logger = logging.getLogger(__name__)
_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client()
        session_file = Path("instagram_session.json")
        if session_file.exists():
            _client.load_settings(session_file)
            try:
                _client.get_timeline_feed()
            except LoginRequired:
                _client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                _client.dump_settings(session_file)
        else:
            _client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            _client.dump_settings(session_file)
    return _client


def post_photo(image_path: str, caption: str) -> str:
    """이미지 피드 포스팅. 업로드된 미디어 PK 반환."""
    cl = get_client()
    media = cl.photo_upload(Path(image_path), caption=caption)
    logger.info("Instagram photo posted: %s", media.pk)
    return str(media.pk)


def post_reel(video_path: str, caption: str, thumbnail_path: str | None = None) -> str:
    """릴스 업로드. 업로드된 미디어 PK 반환."""
    cl = get_client()
    thumb = Path(thumbnail_path) if thumbnail_path else None
    media = cl.clip_upload(Path(video_path), caption=caption, thumbnail=thumb)
    logger.info("Instagram reel posted: %s", media.pk)
    return str(media.pk)


def post_carousel(image_paths: list[str], caption: str) -> str:
    """다중 이미지 캐러셀 포스팅."""
    cl = get_client()
    paths = [Path(p) for p in image_paths]
    media = cl.album_upload(paths, caption=caption)
    logger.info("Instagram carousel posted: %s", media.pk)
    return str(media.pk)
