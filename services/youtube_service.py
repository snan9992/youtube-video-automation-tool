import os
from typing import Dict, Optional


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Dict[str, str]:
    """Upload a video to YouTube if credentials are available."""
    if not client_id or not client_secret:
        return {"status": "skipped", "message": "YouTube credentials are not configured."}

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        import json

        refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        if not refresh_token:
            return {"status": "skipped", "message": "YOUTUBE_REFRESH_TOKEN is missing."}

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
        )
        if not creds.valid:
            creds.refresh(Request())

        service = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["youtube automation", "ai video", "automation"],
                "categoryId": "22",
            },
            "status": {"privacyStatus": "private"},
        }
        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        request = service.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
        response = request.execute()
        return {"status": "uploaded", "message": str(response.get("id", "unknown"))}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
