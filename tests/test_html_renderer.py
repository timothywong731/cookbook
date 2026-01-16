from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from cookbook.html_renderer import render_recipe_html, write_recipe_html
from cookbook.models import Recipe


def test_render_recipe_html():
    """Test that render_recipe_html correctly formats the template."""
    # Arrange
    recipe = Recipe(
        dish_name="Test Dish",
        ingredients=["1 cup of test"],
        cooking_steps=["Step 1"],
        preparation_time="5 min",
        description="A test description"
    )
    illustration_path = Path("test_illustration.png")
    
    # Act
    html = render_recipe_html(recipe, illustration_path)
    
    # Assert
    assert "Test Dish" in html
    assert "1 cup of test" in html
    assert "Step 1" in html
    assert "test_illustration.png" in html
    assert "A test description" in html


def test_write_recipe_html():
    """Test write_recipe_html writes content to the specified path."""
    # Arrange
    mock_path = MagicMock(spec=Path)
    content = "<html>Test</html>"
    
    # Act
    result = write_recipe_html(mock_path, content)
    
    # Assert
    mock_path.write_text.assert_called_once_with(content, encoding="utf-8")
    assert result == mock_path
