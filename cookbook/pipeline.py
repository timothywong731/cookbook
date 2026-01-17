from __future__ import annotations

import datetime
import json
import logging
import re
from pathlib import Path

import openai
from cookbook.ai import (
    build_client,
    build_image_client,
    derive_style_prompt,
    extract_recipe,
    generate_illustration,
)
from cookbook.config import AppConfig, ensure_output_dirs
from cookbook.image_processing import split_to_aspect_ratio
from cookbook.html_renderer import render_recipe_html, write_recipe_html, rebuild_index


logger = logging.getLogger(__name__)


def run_pipeline(config: AppConfig) -> list[Path]:
    """Run the end-to-end recipe generation pipeline.

    Args:
        config: Application configuration containing input/output paths and AI credentials.

    Returns:
        List[Path]: A list of paths to the generated recipe files (JSON and optionally HTML).

    Raises:
        ValueError: If no photos are found in the input directory or no reference style images exist.
    """

    # Prepare output directories and gather source images.
    dirs = ensure_output_dirs(config.output_dir)

    # Search for common image formats in the input directory.
    source_photo_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        source_photo_paths.extend(config.input_dir.glob(ext))

    # Identify already processed photos from existing JSON output in the recipes folder.
    # We look inside each JSON for the 'source_photo' field.
    processed_photos = set()
    for json_file in dirs["recipes"].glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if data.get("source_photo"):
                processed_photos.add(data["source_photo"])
        except (json.JSONDecodeError, IOError):
            continue

    if processed_photos:
        initial_count = len(source_photo_paths)
        source_photo_paths = [p for p in source_photo_paths if p.name not in processed_photos]
        skipped = initial_count - len(source_photo_paths)
        if skipped > 0:
            logger.info(f"Skipping {skipped} already processed photos.")

    if not source_photo_paths:
        logger.info("No new photos to process.")
        return []

    # Load reference images to guide the AI's artistic style.
    reference_images = list(config.reference_style_dir.glob("*.jpg")) + list(
        config.reference_style_dir.glob("*.png")
    )
    if not reference_images:
        raise ValueError(
            "No reference images found for watercolor style in reference_style directory."
        )

    # Initialize the AI clients for recipe extraction and image generation.
    # We use separate configs for chat and images to support FLUX on Serverless APIs.
    client = build_client(
        config.azure_openai_endpoint,
        config.azure_openai_api_key,
        config.azure_openai_api_version,
    )
    image_client = build_image_client(
        config.azure_openai_image_endpoint,
        config.azure_openai_image_api_key,
        config.azure_openai_api_version,
    )

    # Generate a descriptive style prompt based on visual reference images.
    style_prompt = derive_style_prompt(
        client, config.azure_openai_chat_deployment, reference_images
    )

    # Process each source photo: split it, extract a single recipe from all splits, and illustrate.
    output_paths = []
    for photo_path in source_photo_paths:
        try:
            logger.info(f"Processing photo: {photo_path.name}")
            # 1. Split the single source photo into multiple aspect-ratio-friendly crops.
            # We group these splits so the AI can see the entire recipe page across multiple images.
            splits = split_to_aspect_ratio(
                photo_path,
                dirs["splits"],
                config.aspect_ratio,
                config.split_margin_ratio,
            )
            
            # 2. Extract recipe text by passing ALL splits for this specific photo to the AI.
            recipe = extract_recipe(
                client, 
                config.azure_openai_chat_deployment, 
                splits,
                language=config.language
            )
            recipe.source_photo = photo_path.name
            logger.info(f"Extracted recipe: {recipe.dish_name}")

            # Create a sanitized base filename: YYYYMMDD_DishNameInCamelCase
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            # Support Unicode characters (e.g. Chinese) while sanitizing for filenames
            words = re.sub(r"[^\w]|_", " ", recipe.dish_name).split()
            dish_slug = "".join(word.capitalize() for word in words)
            base_filename = f"{date_str}_{dish_slug}"
            
            # 3. Generate an AI illustration matching the watercolor style.
            # Illustration is saved in the same 'recipes' directory.
            # We pass the recipe, source splits, and style references to FLUX.2-pro for realistic generation.
            illustration_path = generate_illustration(
                image_client,
                config.azure_openai_image_deployment,
                recipe, 
                style_prompt,
                splits,
                reference_images,
                dirs["recipes"] / f"{base_filename}_illustration.png",
            )
            
            # 4. Save the final documents in the consolidated 'recipes' directory.
            # We always save the structured JSON.
            json_path = dirs["recipes"] / f"{base_filename}.json"
            json_path.write_text(recipe.model_dump_json(indent=4), encoding="utf-8")
            output_paths.append(json_path)

            # 5. Optionally save the artistic HTML.
            if config.export_html:
                html = render_recipe_html(recipe, illustration_path)
                html_path = dirs["recipes"] / f"{base_filename}.html"
                write_recipe_html(html_path, html)
                output_paths.append(html_path)

            logger.info(f"Successfully generated recipe documents for: {recipe.dish_name}")
        except openai.BadRequestError as e:
            if "content_filter" in str(e):
                logger.error(f"Content filter violation for {photo_path.name}. Skipping. Error: {e}")
            else:
                logger.error(f"Bad request for {photo_path.name}. Skipping. Error: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing {photo_path.name}: {e}")
            continue

    # Rebuild the gallery index after all recipes are processed
    rebuild_index(dirs["recipes"])

    return output_paths
