from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

from cookbook.export_html import export_all, main
from cookbook.models import Recipe


def test_export_all_success():
    """Test export_all processes JSON files and generates HTML."""
    # Arrange
    mock_recipes_dir = MagicMock(spec=Path)
    mock_json_path = MagicMock(spec=Path)
    mock_json_path.name = "recipe1.json"
    mock_json_path.stem = "recipe1"
    mock_json_path.parent = mock_recipes_dir
    mock_json_path.with_suffix.return_value = Path("recipe1.html")
    
    mock_recipes_dir.glob.return_value = [mock_json_path]
    
    # Mock Recipe and its validation
    mock_recipe = MagicMock(spec=Recipe)
    
    with patch("cookbook.export_html.Recipe.model_validate_json", return_value=mock_recipe), \
         patch.object(Path, "read_text", return_value='{"mock": "json"}'), \
         patch.object(Path, "exists", return_value=True), \
         patch("cookbook.export_html.render_recipe_html") as mock_render, \
         patch("cookbook.export_html.write_recipe_html") as mock_write, \
         patch("builtins.print") as mock_print:
        
        mock_render.return_value = "<html>Test</html>"

        # Act
        export_all(mock_recipes_dir)

        # Assert
        mock_recipes_dir.glob.assert_called_once_with("*.json")
        mock_render.assert_called_once()
        mock_write.assert_called_once_with(Path("recipe1.html"), "<html>Test</html>")
        # Verify success print was called (last call)
        mock_print.assert_any_call("  Generated recipe1.html")


def test_export_all_handles_error():
    """Test export_all continues processing if one file fails."""
    # Arrange
    mock_recipes_dir = MagicMock(spec=Path)
    mock_json_path = MagicMock(spec=Path)
    mock_json_path.name = "fail.json"
    mock_recipes_dir.glob.return_value = [mock_json_path]
    
    with patch("cookbook.export_html.Recipe.model_validate_json", side_effect=ValueError("Invalid JSON")), \
         patch.object(Path, "read_text", return_value='{}'), \
         patch("builtins.print") as mock_print:
        
        # Act
        export_all(mock_recipes_dir)

        # Assert
        # Should print the error message
        mock_print.assert_any_call("  Error processing fail.json: Invalid JSON")


def test_export_html_main_execution():
    """Test the main entry point for export_html."""
    # Arrange
    with patch("cookbook.export_html.argparse.ArgumentParser.parse_args") as mock_parse, \
         patch("cookbook.export_html.export_all") as mock_export_all, \
         patch.object(Path, "exists", return_value=True):
        
        mock_parse.return_value = argparse.Namespace(dir="output/recipes")

        # Act
        main()

        # Assert
        mock_parse.assert_called_once()
        mock_export_all.assert_called_once_with(Path("output/recipes"))
