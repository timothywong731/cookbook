from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from cookbook.config import GooglePhotosConfig

SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]


@dataclass
class GooglePhotosClient:
    config: GooglePhotosConfig

    def iter_album_photos(self, album_title: str) -> Iterator[Path]:
        service = self._service()
        album_id = self._find_album_id(service, album_title)
        if album_id is None:
            raise ValueError(f"Album '{album_title}' not found.")
        for media_item in self._iter_media_items(service, album_id):
            yield self._download_media_item(service, media_item)

    def _service(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            self.config.credentials_path, SCOPES
        )
        creds = flow.run_local_server(port=0)
        return build("photoslibrary", "v1", credentials=creds, static_discovery=False)

    def _find_album_id(self, service, title: str) -> str | None:
        next_page_token = None
        while True:
            response = service.albums().list(pageToken=next_page_token).execute()
            for album in response.get("albums", []):
                if album.get("title") == title:
                    return album.get("id")
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                return None

    def _iter_media_items(self, service, album_id: str):
        next_page_token = None
        while True:
            response = (
                service.mediaItems()
                .search(
                    body={"albumId": album_id, "pageToken": next_page_token, "pageSize": 100}
                )
                .execute()
            )
            for item in response.get("mediaItems", []):
                yield item
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                return

    def _download_media_item(self, service, item: dict) -> Path:
        filename = item.get("filename", "photo.jpg")
        download_dir = Path("downloads")
        download_dir.mkdir(parents=True, exist_ok=True)
        path = download_dir / filename
        request = service.mediaItems().get(mediaItemId=item["id"])
        fh = path.open("wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.close()
        return path
