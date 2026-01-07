from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field


class Recipe(BaseModel):
    dish_name: str = Field(..., description="Name of the dish.")
    ingredients: list[str] = Field(..., description="Ingredient list.")
    cooking_steps: list[str] = Field(..., description="Step-by-step cooking instructions.")
    preparation_time: str = Field(..., description="Estimated preparation time.")
    tips: list[str] = Field(..., description="Optional tips for the recipe.")


@dataclass
class RecipeMarkdownWriter:
    output_dir: Path

    def write(self, recipe: Recipe, illustration_path: Path) -> Path:
        safe_name = recipe.dish_name.strip().replace(" ", "_").lower()
        path = self.output_dir / f"{safe_name}.md"
        content = "\n".join(
            [
                f"# {recipe.dish_name}",
                "",
                f"![{recipe.dish_name}]({illustration_path.as_posix()})",
                "",
                "## Preparation Time",
                recipe.preparation_time,
                "",
                "## Ingredients",
                *[f"- {item}" for item in recipe.ingredients],
                "",
                "## Cooking Steps",
                *[f"{index}. {step}" for index, step in enumerate(recipe.cooking_steps, 1)],
                "",
                "## Tips",
                *[f"- {tip}" for tip in recipe.tips],
                "",
            ]
        )
        path.write_text(content, encoding="utf-8")
        return path
