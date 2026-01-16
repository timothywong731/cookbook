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
