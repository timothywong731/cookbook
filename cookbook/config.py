from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class GooglePhotosConfig:
    credentials_path: str
    token_path: str
    recipe_album: str


@dataclass(frozen=True)
class AzureOpenAIConfig:
    endpoint: str
    api_key: str
    api_version: str
    recipe_model: str
    image_model: str
    recipe_prompt: str
    image_prompt: str


@dataclass(frozen=True)
class ImageConfig:
    target_aspect_ratio: float
    margin_ratio: float


@dataclass(frozen=True)
class AppConfig:
    google: GooglePhotosConfig
    azure_openai: AzureOpenAIConfig
    image: ImageConfig
    output_dir: str
    reference_style_dir: str

    @staticmethod
    def from_env() -> "AppConfig":
        return AppConfig(
            google=GooglePhotosConfig(
                credentials_path=os.getenv(
                    "GOOGLE_PHOTOS_CREDENTIALS_PATH", "credentials.json"
                ),
                token_path=os.getenv("GOOGLE_PHOTOS_TOKEN_PATH", "token.json"),
                recipe_album=os.getenv("GOOGLE_PHOTOS_RECIPE_ALBUM", "recipe"),
            ),
            azure_openai=AzureOpenAIConfig(
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                recipe_model=os.getenv("AZURE_OPENAI_RECIPE_MODEL", "gpt-4o"),
                image_model=os.getenv("AZURE_OPENAI_IMAGE_MODEL", "gpt-image-1"),
                recipe_prompt=os.getenv(
                    "AZURE_OPENAI_RECIPE_PROMPT",
                    "Extract the recipe details from the provided image.",
                ),
                image_prompt=os.getenv(
                    "AZURE_OPENAI_IMAGE_PROMPT",
                    "Create a consistent watercolor-style illustration of the dish.",
                ),
            ),
            image=ImageConfig(
                target_aspect_ratio=float(
                    os.getenv("TARGET_IMAGE_ASPECT_RATIO", "1.3333")
                ),
                margin_ratio=float(os.getenv("IMAGE_MARGIN_RATIO", "0.05")),
            ),
            output_dir=os.getenv("OUTPUT_DIR", "outputs"),
            reference_style_dir=os.getenv("REFERENCE_STYLE_DIR", "reference_style"),
        )
