from __future__ import annotations

from pathlib import Path
from typing import Iterable

import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]


def build_photos_service(credentials_path: Path, token_path: Path):
    """Build a Google Photos API service client.

    Args:
        credentials_path: Path to the OAuth client secrets JSON.
        token_path: Path to store/reuse the OAuth token JSON.

    Returns:
        Google Photos service client.
    """

    # Load or refresh OAuth credentials.
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build("photoslibrary", "v1", credentials=creds, static_discovery=False)


def find_album_id(service, album_name: str) -> str:
    """Find the album ID for a given album name.

    Args:
        service: Google Photos API service client.
        album_name: Album title to search for.

    Returns:
        Album ID matching the provided name.

    Raises:
        ValueError: If the album is not found.
    """

    # Paginate through album listings until found.
    next_page_token = None
    while True:
        response = (
            service.albums()
            .list(pageSize=50, pageToken=next_page_token)
            .execute()
        )
        for album in response.get("albums", []):
            if album.get("title") == album_name:
                return album["id"]
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    raise ValueError(f"Album '{album_name}' not found in Google Photos.")


def iter_media_items(service, album_id: str) -> Iterable[dict]:
    """Yield media items for an album.

    Args:
        service: Google Photos API service client.
        album_id: Album ID to list media from.

    Yields:
        Media item dictionaries.
    """

    # Stream through media items using pagination.
    next_page_token = None
    while True:
        response = (
            service.mediaItems()
            .search(
                body={
                    "albumId": album_id,
                    "pageSize": 100,
                    "pageToken": next_page_token,
                }
            )
            .execute()
        )
        for item in response.get("mediaItems", []):
            yield item
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break


def download_media_item(media_item: dict, output_dir: Path) -> Path:
    """Download a single media item to disk.

    Args:
        media_item: Media item metadata from the API.
        output_dir: Directory to save the download.

    Returns:
        Path to the downloaded image file.
    """

    # Download the original image file.
    filename = media_item.get("filename") or f"photo_{media_item['id']}.jpg"
    base_url = media_item["baseUrl"]
    output_path = output_dir / filename
    response = requests.get(f"{base_url}=d", timeout=30)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def download_album_photos(
    credentials_path: Path, token_path: Path, album_name: str, output_dir: Path
) -> list[Path]:
    """Download all photos from a Google Photos album.

    Args:
        credentials_path: Path to OAuth client secrets JSON.
        token_path: Path to OAuth token JSON.
        album_name: Name of the album to download.
        output_dir: Directory to save downloaded photos.

    Returns:
        List of image paths downloaded from the album.
    """

    # Build the API client and download album items.
    service = build_photos_service(credentials_path, token_path)
    album_id = find_album_id(service, album_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for item in iter_media_items(service, album_id):
        paths.append(download_media_item(item, output_dir))
    return paths
