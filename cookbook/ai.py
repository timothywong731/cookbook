from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from openai import AzureOpenAI

from cookbook.config import AzureOpenAIConfig
from cookbook.recipe import Recipe


@dataclass
class AzureOpenAIRecipeExtractor:
    config: AzureOpenAIConfig

    def extract(self, image_paths: Iterable[Path]) -> Recipe:
        client = self._client()
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You are an expert chef transcribing recipes from images. "
                            "Return structured data only."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.config.recipe_prompt},
                    *[self._image_payload(path) for path in image_paths],
                ],
            },
        ]
        response = client.beta.chat.completions.parse(
            model=self.config.recipe_model,
            messages=messages,
            response_format=Recipe,
        )
        return response.choices[0].message.parsed

    def _client(self) -> AzureOpenAI:
        return AzureOpenAI(
            azure_endpoint=self.config.endpoint,
            api_key=self.config.api_key,
            api_version=self.config.api_version,
        )

    @staticmethod
    def _image_payload(path: Path) -> dict:
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
        }


@dataclass
class WatercolorIllustrator:
    config: AzureOpenAIConfig
    reference_dir: Path
    output_dir: Path

    def generate(self, recipe: Recipe, dish_photo: Path) -> Path:
        client = self._client()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        prompt = self._build_prompt(recipe)
        images = client.images.generate(
            model=self.config.image_model,
            prompt=prompt,
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
        image_bytes = base64.b64decode(images.data[0].b64_json)
        output_path = (
            self.output_dir / f"{recipe.dish_name.strip().replace(' ', '_')}.png"
        )
        output_path.write_bytes(image_bytes)
        return output_path

    def _build_prompt(self, recipe: Recipe) -> str:
        references = ", ".join(self._reference_names())
        return (
            f"{self.config.image_prompt}\n"
            f"Dish: {recipe.dish_name}\n"
            f"Ingredients: {', '.join(recipe.ingredients)}\n"
            f"Style references: {references}"
        )

    def _reference_names(self) -> list[str]:
        if not self.reference_dir.exists():
            return []
        return [path.name for path in self.reference_dir.glob("*") if path.is_file()]

    def _client(self) -> AzureOpenAI:
        return AzureOpenAI(
            azure_endpoint=self.config.endpoint,
            api_key=self.config.api_key,
            api_version=self.config.api_version,
        )
