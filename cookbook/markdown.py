from __future__ import annotations

import urllib.parse
from pathlib import Path

from cookbook.models import Recipe


def render_recipe_markdown(recipe: Recipe, illustration_path: Path) -> str:
    """Render a recipe as markdown.

    Args:
        recipe: Recipe data to render.
        illustration_path: Path to the generated illustration.

    Returns:
        Markdown representation of the recipe.
    """

    # Build markdown sections from recipe fields.
    ingredients = "\n".join(f"- {item}" for item in recipe.ingredients)
    steps = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(recipe.cooking_steps)
    )
    tips = "\n".join(f"- {tip}" for tip in recipe.tips) if recipe.tips else "-"
    
    # Use only the filename as a relative path, since markdown and image share a directory.
    # Encode spaces and special characters for the HTML src attribute.
    illustration_ref = urllib.parse.quote(illustration_path.name)
    
    return (
        f'<img src="{illustration_ref}" align="right" width="400" style="margin-left: 20px;">\n\n'
        f"# {recipe.dish_name}\n\n"
        f"**Preparation time:** {recipe.preparation_time}\n\n"
        f"## Ingredients\n{ingredients}\n\n"
        f"## Steps\n{steps}\n\n"
        f"## Tips\n{tips}\n"
    )


def write_recipe_markdown(output_path: Path, content: str) -> Path:
    """Write a markdown string to disk.

    Args:
        output_path: Destination path for the markdown file.
        content: Markdown content to write.

    Returns:
        Path to the written markdown file.
    """

    # Persist markdown to the filesystem.
    output_path.write_text(content, encoding="utf-8")
    return output_path
