from __future__ import annotations

from pathlib import Path

from cookbook.ai import (
    build_client,
    build_image_client,
    derive_style_prompt,
    extract_recipe,
    generate_illustration,
)
from cookbook.config import AppConfig, ensure_output_dirs
from cookbook.image_processing import split_to_aspect_ratio
from cookbook.markdown import render_recipe_markdown, write_recipe_markdown


def run_pipeline(config: AppConfig) -> list[Path]:
    """Run the end-to-end recipe generation pipeline.

    Args:
        config: Application configuration containing input/output paths and AI credentials.

    Returns:
        List[Path]: A list of paths to the generated markdown recipe files.

    Raises:
        ValueError: If no photos are found in the input directory or no reference style images exist.
    """

    # Prepare output directories and gather source images.
    dirs = ensure_output_dirs(config.output_dir)

    # Search for common image formats in the input directory.
    source_photo_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        source_photo_paths.extend(config.input_dir.glob(ext))

    if not source_photo_paths:
        raise ValueError(f"No photos found in input directory: {config.input_dir}")

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
    markdown_paths = []
    for photo_path in source_photo_paths:
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
        
        # 3. Generate an AI illustration matching the watercolor style.
        # Illustration is saved in the same 'recipes' directory as the markdown.
        # We pass the recipe, source splits, and style references to FLUX.2-pro for realistic generation.
        illustration_path = generate_illustration(
            image_client,
            config.azure_openai_image_deployment,
            recipe,
            style_prompt,
            splits,
            reference_images,
            dirs["recipes"] / f"{photo_path.stem}_illustration.png",
        )
        
        # 4. Format the recipe and illustration link into markdown.
        markdown = render_recipe_markdown(recipe, illustration_path)
        
        # 5. Save the final markdown document in the consolidated 'recipes' directory.
        output_path = dirs["recipes"] / f"{photo_path.stem}.md"
        markdown_paths.append(write_recipe_markdown(output_path, markdown))

    return markdown_paths
