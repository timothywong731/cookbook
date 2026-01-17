from __future__ import annotations

import urllib.parse
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from cookbook.models import Recipe


def render_recipe_html(recipe: Recipe, illustration_path: Path) -> str:
    """Render a recipe as artistic HTML for printing.

    Args:
        recipe: Recipe data to render.
        illustration_path: Path to the generated illustration.

    Returns:
        HTML string.
    """

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("recipe.html")

    illustration_url = urllib.parse.quote(illustration_path.name)

    return template.render(
        recipe=recipe,
        illustration_url=illustration_url
    )


def render_index_html(items: list[dict]) -> str:
    """Render a gallery index page for all recipes.

    Args:
        items: List of dicts with dish_name, html_filename, illustration_filename, etc.

    Returns:
        HTML string.
    """
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("index.html")
    # Sort items by dish_name alphabetically
    sorted_items = sorted(items, key=lambda x: x["dish_name"])
    return template.render(items=sorted_items)


def rebuild_index(recipes_dir: Path) -> Path | None:
    """Scan the recipes directory and generate an index.html file.

    Args:
        recipes_dir: Directory containing .json and .html files.

    Returns:
        Path to the generated index.html or None if no recipes found.
    """
    json_files = list(recipes_dir.glob("*.json"))
    if not json_files:
        return None

    index_items = []
    for json_path in json_files:
        html_path = json_path.with_suffix(".html")
        illustration_path = json_path.parent / f"{json_path.stem}_illustration.png"

        if html_path.exists() and illustration_path.exists():
            try:
                recipe = Recipe.model_validate_json(json_path.read_text(encoding="utf-8"))
                index_items.append({
                    "dish_name": recipe.dish_name,
                    "html_filename": html_path.name,
                    "illustration_filename": illustration_path.name,
                    "prep_time": recipe.preparation_time,
                    "servings": recipe.servings
                })
            except Exception as e:
                print(f"Warning: Could not include {json_path.name} in index: {e}")
                continue

    if not index_items:
        return None

    index_html = render_index_html(index_items)
    index_path = recipes_dir / "index.html"
    return write_recipe_html(index_path, index_html)


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
