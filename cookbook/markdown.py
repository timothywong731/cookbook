from __future__ import annotations

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
    illustration_ref = illustration_path.as_posix()
    return (
        f"# {recipe.dish_name}\n\n"
        f"![Illustration]({illustration_ref})\n\n"
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
