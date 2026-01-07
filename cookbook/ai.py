from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Iterable

from openai import AzureOpenAI

from cookbook.models import Recipe

SYSTEM_RECIPE_PROMPT = (
    "You extract recipes from images and respond with JSON that matches the schema. "
    "Do not include any commentary."
)

STYLE_PROMPT = (
    "Summarize the watercolor style from the reference images. "
    "Focus on color palette, brush texture, lighting, and composition."
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
    """Create an Azure OpenAI client.

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


def extract_recipe(
    client: AzureOpenAI,
    deployment: str,
    image_path: Path,
) -> Recipe:
    """Extract structured recipe data from an image.

    Args:
        client: Azure OpenAI client.
        deployment: Chat deployment name.
        image_path: Path to the recipe image.

    Returns:
        Parsed Recipe model.
    """

    # Send the image to the chat model for extraction.
    payload = {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{_encode_image(image_path)}"},
    }
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": SYSTEM_RECIPE_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the recipe details."},
                    payload,
                ],
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("No recipe content returned from Azure OpenAI.")
    return Recipe.model_validate(json.loads(content))


def derive_style_prompt(
    client: AzureOpenAI,
    deployment: str,
    reference_images: Iterable[Path],
) -> str:
    """Derive a watercolor style prompt from reference images.

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
        temperature=0.3,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("No style prompt returned from Azure OpenAI.")
    return content.strip()


def generate_illustration(
    client: AzureOpenAI,
    deployment: str,
    dish_name: str,
    style_prompt: str,
    output_path: Path,
) -> Path:
    """Generate a watercolor illustration for a dish.

    Args:
        client: Azure OpenAI client.
        deployment: Image deployment name.
        dish_name: Name of the dish to illustrate.
        style_prompt: Style prompt derived from reference images.
        output_path: Path to write the generated illustration.

    Returns:
        Path to the generated illustration image.
    """

    # Build the prompt and write the generated image to disk.
    prompt = (
        f"Watercolor illustration of {dish_name}. "
        f"{style_prompt}. Clean background, recipe book style."
    )
    response = client.images.generate(
        model=deployment,
        prompt=prompt,
        size="1024x1024",
    )
    image_data = base64.b64decode(response.data[0].b64_json)
    output_path.write_bytes(image_data)
    return output_path
