from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cookbook.ai import AzureOpenAIRecipeExtractor, WatercolorIllustrator
from cookbook.config import AppConfig
from cookbook.images import ImagePreprocessor
from cookbook.photos import GooglePhotosClient
from cookbook.recipe import RecipeMarkdownWriter


@dataclass
class CookbookPipeline:
    config: AppConfig = AppConfig.from_env()

    def run(self) -> None:
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        photos_client = GooglePhotosClient(self.config.google)
        preprocessor = ImagePreprocessor(
            target_aspect_ratio=self.config.image.target_aspect_ratio,
            margin_ratio=self.config.image.margin_ratio,
            output_dir=output_dir / "preprocessed",
        )
        extractor = AzureOpenAIRecipeExtractor(self.config.azure_openai)
        illustrator = WatercolorIllustrator(
            self.config.azure_openai,
            reference_dir=Path(self.config.reference_style_dir),
            output_dir=output_dir / "illustrations",
        )
        writer = RecipeMarkdownWriter(output_dir=output_dir)

        for photo in photos_client.iter_album_photos(self.config.google.recipe_album):
            prepared_images = preprocessor.prepare(photo)
            recipe = extractor.extract(prepared_images)
            illustration_path = illustrator.generate(
                recipe=recipe,
                dish_photo=prepared_images[0],
            )
            writer.write(recipe, illustration_path)
