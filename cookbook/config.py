from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Configuration for the recipe generation pipeline.

    Attributes:
        input_dir: Directory containing input recipe photos.
        output_dir: Base directory for pipeline outputs.
        aspect_ratio: Target aspect ratio for preprocessing.
        split_margin_ratio: Overlap ratio when splitting images.
        azure_openai_endpoint: Azure OpenAI endpoint.
        azure_openai_api_key: Azure OpenAI API key.
        azure_openai_api_version: Azure OpenAI API version.
        azure_openai_chat_deployment: Azure OpenAI chat deployment name.
        azure_openai_image_endpoint: Azure OpenAI image endpoint (for FLUX/DALL-E).
        azure_openai_image_api_key: Azure OpenAI image API key.
        azure_openai_image_deployment: Azure OpenAI image deployment name.
        reference_style_dir: Directory containing reference style images.
        language: Target language for the recipe extraction.
        export_html: Whether to export recipes as HTML files.
    """

    # Pipeline configuration values.
    input_dir: Path
    output_dir: Path
    aspect_ratio: float
    split_margin_ratio: float
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str
    azure_openai_chat_deployment: str
    azure_openai_image_endpoint: str
    azure_openai_image_api_key: str
    azure_openai_image_deployment: str
    reference_style_dir: Path
    language: str
    export_html: bool


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
    # We consolidate markdown and illustrations into a single 'recipes' directory.
    splits_dir = base_dir / "splits"
    recipes_dir = base_dir / "recipes"
    
    for path in (splits_dir, recipes_dir):
        path.mkdir(parents=True, exist_ok=True)
        
    return {
        "splits": splits_dir,
        "recipes": recipes_dir,
    }
