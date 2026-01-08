from pathlib import Path

from cookbook.markdown import render_recipe_markdown, write_recipe_markdown
from cookbook.models import Recipe


def test_render_recipe_markdown_includes_fields(tmp_path: Path) -> None:
    """Ensure markdown output includes key recipe fields."""

    # Build a sample recipe for rendering.
    recipe = Recipe(
        dish_name="Sample Dish",
        ingredients=["1 egg", "2 tomatoes"],
        cooking_steps=["Mix ingredients", "Cook"],
        preparation_time="20 minutes",
        tips=["Serve warm"],
    )
    illustration_path = tmp_path / "illustration.png"
    illustration_path.write_text("placeholder", encoding="utf-8")

    markdown = render_recipe_markdown(recipe, illustration_path)

    assert "# Sample Dish" in markdown
    assert "**Preparation time:** 20 minutes" in markdown
    assert "- 1 egg" in markdown
    assert "1. Mix ingredients" in markdown
    assert "## Tips" in markdown
    assert '<img src="illustration.png" align="right"' in markdown


def test_write_recipe_markdown(tmp_path: Path) -> None:
    """Ensure markdown content is written to disk correctly."""
    output_path = tmp_path / "test.md"
    content = "# Test Recipe"
    
    written_path = write_recipe_markdown(output_path, content)
    
    assert written_path == output_path
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == content
