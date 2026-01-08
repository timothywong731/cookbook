from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Iterable

from openai import AzureOpenAI, OpenAI

from cookbook.models import Recipe

SYSTEM_RECIPE_PROMPT = (
    "You extract recipes from images and respond with JSON that matches the schema. "
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
        f"A beautiful illustration of {recipe.dish_name}. "
        f"The dish features {visual_context}. "
        f"{style_prompt}. "
        f"Clean white background, professional cookbook illustration style, soft lighting, appetizing composition. "
        f"No text in the image. No watermarks. "
        f"High detail and resolution. Focus entirely on the main dish. "
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
    response = client.images.generate(
        model=deployment,
        prompt=prompt,
        size="1024x1024",
        extra_body={
            "input_images": input_payloads,
            "style_images": style_payloads,
        }
    )
    
    # Save the resulting image to the specified local path.
    image_data = base64.b64decode(response.data[0].b64_json)
    output_path.write_bytes(image_data)
    return output_path
