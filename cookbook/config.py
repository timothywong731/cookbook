from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Configuration for the recipe generation pipeline.

    Attributes:
        album_name: Google Photos album name.
        output_dir: Base directory for pipeline outputs.
        aspect_ratio: Target aspect ratio for preprocessing.
        split_margin_ratio: Overlap ratio when splitting images.
        credentials_path: Path to Google OAuth client secrets.
        token_path: Path to cached Google OAuth token.
        azure_openai_endpoint: Azure OpenAI endpoint.
        azure_openai_api_key: Azure OpenAI API key.
        azure_openai_api_version: Azure OpenAI API version.
        azure_openai_chat_deployment: Azure OpenAI chat deployment name.
        azure_openai_image_deployment: Azure OpenAI image deployment name.
        reference_style_dir: Directory containing reference style images.
    """

    # Pipeline configuration values.
    album_name: str
    output_dir: Path
    aspect_ratio: float
    split_margin_ratio: float
    credentials_path: Path
    token_path: Path
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str
    azure_openai_chat_deployment: str
    azure_openai_image_deployment: str
    reference_style_dir: Path


DEFAULT_ASPECT_RATIO = 4 / 5
DEFAULT_MARGIN_RATIO = 0.08


def ensure_output_dirs(base_dir: Path) -> dict[str, Path]:
    """Create output directories used by the pipeline.

    Args:
        base_dir: Base output directory.

    Returns:
        A mapping of directory names to paths.
    """

    # Ensure each output subdirectory exists.
    photos_dir = base_dir / "photos"
    splits_dir = base_dir / "splits"
    illustrations_dir = base_dir / "illustrations"
    markdown_dir = base_dir / "markdown"
    for path in (photos_dir, splits_dir, illustrations_dir, markdown_dir):
        path.mkdir(parents=True, exist_ok=True)
    return {
        "photos": photos_dir,
        "splits": splits_dir,
        "illustrations": illustrations_dir,
        "markdown": markdown_dir,
    }
