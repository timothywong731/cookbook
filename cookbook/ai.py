from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Iterable

import openai
from openai import AzureOpenAI, OpenAI

from cookbook.models import Recipe

logger = logging.getLogger(__name__)

SYSTEM_RECIPE_PROMPT = (
    "You extract recipes from images and respond with JSON that matches the schema. "
    "Fill in as many fields as possible including 'description', 'servings', 'preparation_time', 'cooking_time' and 'tips'. "
    "If a value is not explicitly in the text, you can infer it if it's obvious (e.g. servings based on quantities), "
    "or provide an appropriate estimate. Write the 'description' as a short, appetizing subtitle. "
    "Do not include any commentary."
)

STYLE_PROMPT = (
    "Summarize the artistic style from the reference images. "
    "Focus on color palette, brush texture, lighting, and composition. "
    "Describe the art style in details. Do not mention the content of the images. "
)


def _encode_image(image_path: Path) -> str:
    """Encode an image file as base64.

    Args:
        image_path: Path to the image file.

    Returns:
        Base64-encoded image string.
    """

    # Convert image bytes to base64 for API transport.
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def build_client(endpoint: str, api_key: str, api_version: str) -> AzureOpenAI:
    """Create an Azure OpenAI client for chat/extraction.

    Args:
        endpoint: Azure OpenAI endpoint URL.
        api_key: API key for Azure OpenAI.
        api_version: API version string.

    Returns:
        Configured AzureOpenAI client.
    """

    # Instantiate the Azure OpenAI SDK client.
    return AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint,
    )


def build_image_client(
    endpoint: str, api_key: str, api_version: str
) -> AzureOpenAI | OpenAI:
    """Create a client for image generation (supports Azure OpenAI or Serverless/MaaS).

    Args:
        endpoint: Endpoint URL.
        api_key: API key.
        api_version: API version string (used for Azure OpenAI).

    Returns:
        Configured client (AzureOpenAI or OpenAI).
    """

    # If the endpoint is a Serverless API (MaaS), use the standard OpenAI client.
    # FLUX.2-pro on Azure often uses this format.
    if "models.ai.azure.com" in endpoint:
        # Standardize the endpoint to include /v1 if missing for MaaS.
        base_url = endpoint.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"

        return OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    # Fall back to standard Azure OpenAI (DALL-E).
    return AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint,
    )


def extract_recipe(
    client: AzureOpenAI,
    deployment: str,
    image_paths: list[Path],
    language: str = "English",
) -> Recipe:
    """Extract structured recipe data from one or more images into a target language.

    Args:
        client: Azure OpenAI client.
        deployment: Chat deployment name.
        image_paths: List of paths to the recipe images/splits.
        language: The target language for the extracted recipe text.

    Returns:
        Structured Recipe model.

    Raises:
        ValueError: If no recipe content is returned or parsing fails.
    """

    # Prepare multimodal content containing all image splits for context.
    content: list[dict] = [
        {
            "type": "text", 
            "text": f"Extract the recipe details from these images. Write all text in {language}."
        }
    ]
    
    for path in image_paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{_encode_image(path)}"},
        })

    # Use the beta parse method for native Pydantic structured output.
    response = client.beta.chat.completions.parse(
        model=deployment,
        messages=[
            {"role": "system", "content": SYSTEM_RECIPE_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=1.0,
        response_format=Recipe,
    )

    # Retrieve the automatically parsed Pydantic model.
    recipe = response.choices[0].message.parsed
    if not recipe:
        raise ValueError("Azure OpenAI failed to return a valid recipe structure.")

    return recipe


def derive_style_prompt(
    client: AzureOpenAI,
    deployment: str,
    reference_images: Iterable[Path],
) -> str:
    """Derive a style prompt from reference images.

    Args:
        client: Azure OpenAI client.
        deployment: Chat deployment name.
        reference_images: Reference images for the style prompt.

    Returns:
        A style prompt string.
    """

    # Provide reference images to capture style characteristics.
    image_payloads = [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{_encode_image(image_path)}"
            },
        }
        for image_path in reference_images
    ]
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": STYLE_PROMPT},
            {"role": "user", "content": image_payloads},
        ],
        temperature=1.0,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("No style prompt returned from Azure OpenAI.")
    return content.strip()


def generate_illustration(
    client: AzureOpenAI | OpenAI,
    deployment: str,
    recipe: Recipe,
    style_prompt: str,
    image_paths: list[Path],
    reference_images: Iterable[Path],
    output_path: Path,
) -> Path:
    """Generate an illustration for a dish based on the full recipe and input images.

    Args:
        client: AI client for image generation.
        deployment: Image deployment name (FLUX.2-pro).
        recipe: The complete structured recipe data.
        style_prompt: Style prompt derived from reference images.
        image_paths: List of paths to the source recipe images (splits).
        reference_images: List of paths to the style reference images.
        output_path: Path to write the generated illustration.

    Returns:
        Path to the generated illustration image.
    """

    # Build an enriched prompt that describes the dish visually using its ingredients.
    visual_context = ", ".join(recipe.ingredients[:7])
    
    prompt = (
        f"<dish>{recipe.dish_name}</dish>\n"
        f"<visual_context>{visual_context}</visual_context>\n"
        f"<style>{style_prompt}</style>\n"
        f"<important_instructions>"
        f"Clean white background, professional cookbook illustration style, soft lighting, appetizing composition. "
        f"No text in the image. No watermarks. "
        f"High detail and resolution. Focus entirely on the main dish. "
        f"</important_instructions>\n"
    )

    # Prepare input images and style references for the model.
    # FLUX.2-pro supports image-to-image and style reference via custom parameters.
    input_payloads = [
        f"data:image/jpeg;base64,{_encode_image(p)}" for p in image_paths
    ]
    style_payloads = [
        f"data:image/jpeg;base64,{_encode_image(p)}" for p in reference_images
    ]

    # Request the image generation from the AI model with image-to-image context.
    try:
        response = client.images.generate(
            model=deployment,
            prompt=prompt,
            size="1024x1024",
            extra_body={
                "input_images": input_payloads,
                "style_images": style_payloads,
            }
        )
    except openai.BadRequestError as e:
        error_msg = str(e).lower()
        if "blocklist" in error_msg or "content" in error_msg:
            logger.warning(f"Image generation blocked for '{recipe.dish_name}'. Retrying with simplified prompt.")
            # Simplified prompt: remove ingredients and XML tags which might be confusing the filter.
            simplified_prompt = (
                f"A professional cookbook illustration of {recipe.dish_name}. "
                f"Art style: {style_prompt}. "
                "Clean white background, soft lighting, appetizing composition, high detail, no text."
            )
            try:
                response = client.images.generate(
                    model=deployment,
                    prompt=simplified_prompt,
                    size="1024x1024",
                    extra_body={
                        "input_images": input_payloads,
                        "style_images": style_payloads,
                    }
                )
            except openai.BadRequestError as inner_e:
                # If still blocked, we might need to be even more generic or just fail gracefully.
                # For now, let's try one last extremely generic prompt if it's the dish name itself.
                logger.warning(f"Simplified prompt also blocked. Retrying with generic prompt.")
                generic_prompt = (
                    "A professional watercolor cookbook illustration of a delicious meal. "
                    "Clean white background, soft lighting, appetizing composition."
                )
                response = client.images.generate(
                    model=deployment,
                    prompt=generic_prompt,
                    size="1024x1024",
                    extra_body={
                        "input_images": input_payloads,
                        "style_images": style_payloads,
                    }
                )
        else:
            raise e
    
    # Save the resulting image to the specified local path.
    image_data = base64.b64decode(response.data[0].b64_json)
    output_path.write_bytes(image_data)
    return output_path
