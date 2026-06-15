"""YouTube 영상/쇼츠 자동 업로드"""
import logging
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import YOUTUBE_CLIENT_SECRETS_FILE

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.json"


def get_youtube_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    category_id: str = "22",       # People & Blogs
    privacy: str = "public",        # public / unlisted / private
    is_shorts: bool = False,
) -> str:
    """영상 업로드. 업로드된 YouTube video ID 반환."""
    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy},
    }

    # 쇼츠는 세로(9:16) 영상 + #Shorts 태그 권장
    if is_shorts and "#Shorts" not in description:
        body["snippet"]["description"] += "\n\n#Shorts"

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]
    logger.info("YouTube video uploaded: https://youtu.be/%s", video_id)
    return video_id


def upload_shorts(video_path: str, title: str, description: str, tags: list[str] | None = None) -> str:
    """쇼츠 전용 업로드 (세로 영상 필요)."""
    return upload_video(video_path, title, description, tags=tags, is_shorts=True)
