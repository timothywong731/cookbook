from __future__ import annotations

import urllib.parse
from pathlib import Path

from cookbook.models import Recipe


def render_recipe_html(recipe: Recipe, illustration_path: Path) -> str:
    """Render a recipe as artistic HTML for printing.

    Args:
        recipe: Recipe data to render.
        illustration_path: Path to the generated illustration.

    Returns:
        HTML string.
    """

    template_path = Path(__file__).parent / "templates" / "recipe.html"
    template = template_path.read_text(encoding="utf-8")

    illustration_url = urllib.parse.quote(illustration_path.name)
    
    description_tag = f"<p>{recipe.description}</p>" if recipe.description else ""
    
    ingredients_html = "\n".join(f"<li>{item}</li>" for item in recipe.ingredients)
    steps_html = "\n".join(f"<li>{step}</li>" for step in recipe.cooking_steps)
    
    notes_html = ""
    if recipe.tips:
        tips_content = " ".join(recipe.tips)
        notes_html = f"""
        <div class="notes-area">
            <h3>NOTES</h3>
            <p>{tips_content}</p>
        </div>
        """

    return template.format(
        dish_name=recipe.dish_name,
        description_tag=description_tag,
        illustration_url=illustration_url,
        servings=recipe.servings or "-",
        prep_time=recipe.preparation_time or "-",
        cook_time=recipe.cooking_time or "-",
        ingredients_html=ingredients_html,
        steps_html=steps_html,
        notes_html=notes_html
    )


def write_recipe_html(output_path: Path, content: str) -> Path:
    """Write HTML content to disk.

    Args:
        output_path: Destination path.
        content: HTML string.

    Returns:
        Path to the written file.
    """
    output_path.write_text(content, encoding="utf-8")
    return output_path
