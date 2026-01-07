from __future__ import annotations

from pathlib import Path

from cookbook.ai import (
    build_client,
    derive_style_prompt,
    extract_recipe,
    generate_illustration,
)
from cookbook.config import AppConfig, ensure_output_dirs
from cookbook.google_photos import download_album_photos
from cookbook.image_processing import split_images
from cookbook.markdown import render_recipe_markdown, write_recipe_markdown


def run_pipeline(config: AppConfig) -> list[Path]:
    """Run the end-to-end recipe generation pipeline.

    Args:
        config: Application configuration.

    Returns:
        List of markdown paths generated for each processed image.
    """

    # Prepare output directories and gather source images.
    dirs = ensure_output_dirs(config.output_dir)

    photo_paths = download_album_photos(
        config.credentials_path,
        config.token_path,
        config.album_name,
        dirs["photos"],
    )

    split_paths = split_images(
        photo_paths,
        dirs["splits"],
        config.aspect_ratio,
        config.split_margin_ratio,
    )

    reference_images = list(config.reference_style_dir.glob("*.jpg")) + list(
        config.reference_style_dir.glob("*.png")
    )
    if not reference_images:
        raise ValueError(
            "No reference images found for watercolor style in reference_style directory."
        )

    client = build_client(
        config.azure_openai_endpoint,
        config.azure_openai_api_key,
        config.azure_openai_api_version,
    )
    style_prompt = derive_style_prompt(
        client, config.azure_openai_chat_deployment, reference_images
    )

    markdown_paths = []
    for image_path in split_paths:
        recipe = extract_recipe(client, config.azure_openai_chat_deployment, image_path)
        illustration_path = generate_illustration(
            client,
            config.azure_openai_image_deployment,
            recipe.dish_name,
            style_prompt,
            dirs["illustrations"] / f"{image_path.stem}_illustration.png",
        )
        markdown = render_recipe_markdown(recipe, illustration_path)
        output_path = dirs["markdown"] / f"{image_path.stem}.md"
        markdown_paths.append(write_recipe_markdown(output_path, markdown))

    return markdown_paths
