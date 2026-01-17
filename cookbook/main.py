from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from cookbook.config import AppConfig, DEFAULT_ASPECT_RATIO, DEFAULT_MARGIN_RATIO
from cookbook.pipeline import run_pipeline

# Load dotenv file if present.
from dotenv import load_dotenv
load_dotenv()

def _get_env(name: str) -> str:
    """Fetch a required environment variable.

    Args:
        name: Environment variable name.

    Returns:
        Environment variable value.

    Raises:
        ValueError: If the variable is missing or empty.
    """

    # Ensure required environment variables are present.
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def build_config(args: argparse.Namespace) -> AppConfig:
    """Build application configuration from CLI arguments.

    Args:
        args: Parsed CLI arguments.

    Returns:
        AppConfig instance populated with CLI values and environment variables.
    """

    # Combine CLI inputs with environment configuration.
    return AppConfig(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        aspect_ratio=args.aspect_ratio,
        split_margin_ratio=args.split_margin_ratio,
        azure_openai_endpoint=_get_env("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=_get_env("AZURE_OPENAI_API_KEY"),
        azure_openai_api_version=_get_env("AZURE_OPENAI_API_VERSION"),
        azure_openai_chat_deployment=_get_env("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        azure_openai_image_endpoint=os.getenv("AZURE_OPENAI_IMAGE_ENDPOINT", os.getenv("AZURE_OPENAI_ENDPOINT")),
        azure_openai_image_api_key=os.getenv("AZURE_OPENAI_IMAGE_API_KEY", os.getenv("AZURE_OPENAI_API_KEY")),
        azure_openai_image_deployment=_get_env("AZURE_OPENAI_IMAGE_DEPLOYMENT"),
        reference_style_dir=Path(args.reference_style_dir),
        language=args.language,
        export_html=args.export_html,
    )


def main() -> None:
    """CLI entry point for running the cookbook pipeline."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Configure CLI arguments and execute the pipeline.
    parser = argparse.ArgumentParser(description="Generate a cookbook from recipe photos.")
    parser.add_argument(
        "--input-dir",
        default="input",
        help="Directory containing local recipe photos.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for generated JSON, images, and intermediate files.",
    )
    parser.add_argument(
        "--aspect-ratio",
        type=float,
        default=DEFAULT_ASPECT_RATIO,
        help="Target aspect ratio (width/height) for preprocessing splits.",
    )
    parser.add_argument(
        "--split-margin-ratio",
        type=float,
        default=DEFAULT_MARGIN_RATIO,
        help="Overlap margin ratio when splitting images.",
    )
    parser.add_argument(
        "--reference-style-dir",
        default="reference_style",
        help="Directory containing reference watercolor style images.",
    )
    parser.add_argument(
        "--language",
        default="English",
        help="Target language for the generated recipes.",
    )
    parser.add_argument(
        "--export-html",
        action="store_true",
        help="Whether to export recipes as HTML files.",
    )
    args = parser.parse_args()

    config = build_config(args)

    # Setup basic logging to console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    output_paths = run_pipeline(config)
    for path in output_paths:
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
