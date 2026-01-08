from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cookbook.config import AppConfig
from cookbook.models import Recipe
from cookbook.pipeline import run_pipeline


@pytest.fixture
def mock_config() -> AppConfig:
    """Fixture for a mock AppConfig."""
    return AppConfig(
        input_dir=Path("/mock/input"),
        output_dir=Path("/mock/output"),
        aspect_ratio=0.8,
        split_margin_ratio=0.1,
        azure_openai_endpoint="https://mock.endpoint",
        azure_openai_api_key="mock-key",
        azure_openai_api_version="2023-05-15",
        azure_openai_chat_deployment="chat-deploy",
        azure_openai_image_endpoint="https://mock.image.endpoint",
        azure_openai_image_api_key="mock-image-key",
        azure_openai_image_deployment="image-deploy",
        reference_style_dir=Path("/mock/style"),
        language="English",
    )


def test_run_pipeline_success(mock_config: AppConfig):
    """Test that run_pipeline executes all steps correctly under normal conditions.
    
    This test uses the AAA (Arrange, Act, Assert) pattern with mocks.
    """
    # Arrange
    # Mocking internal components to avoid external API calls and side effects.
    with patch("cookbook.pipeline.ensure_output_dirs") as mock_ensure_dirs, \
         patch("cookbook.pipeline.split_to_aspect_ratio") as mock_split_to_ratio, \
         patch("cookbook.pipeline.build_client") as mock_build_client, \
         patch("cookbook.pipeline.build_image_client") as mock_build_image_client, \
         patch("cookbook.pipeline.derive_style_prompt") as mock_derive_style, \
         patch("cookbook.pipeline.extract_recipe") as mock_extract_recipe, \
         patch("cookbook.pipeline.generate_illustration") as mock_gen_illustration, \
         patch("cookbook.pipeline.render_recipe_markdown") as mock_render_md, \
         patch("cookbook.pipeline.write_recipe_markdown") as mock_write_md, \
         patch.object(Path, "glob") as mock_glob:

        # Set up mock returns
        mock_ensure_dirs.return_value = {
            "splits": Path("/mock/output/splits"),
            "recipes": Path("/mock/output/recipes"),
        }
        
        # Simulate finding photos in the input directory and style directory
        mock_glob.side_effect = [
            [Path("/mock/input/recipe1.jpg")], # first call for photos
            [], # second call for photos (jpeg)
            [], # third call for photos (png)
            [Path("/mock/style/style1.jpg")], # call for reference styles (jpg)
            [] # second call for reference styles (png)
        ]
        
        mock_split_to_ratio.return_value = [
            Path("/mock/output/splits/recipe1_part0.jpg"),
            Path("/mock/output/splits/recipe1_part1.jpg")
        ]
        mock_build_client.return_value = MagicMock()
        mock_build_image_client.return_value = MagicMock()
        mock_derive_style.return_value = "Watercolor style"
        
        mock_recipe = Recipe(
            dish_name="Test Dish", 
            ingredients=["ing1"], 
            cooking_steps=["step1"], 
            preparation_time="10 mins"
        )
        mock_extract_recipe.return_value = mock_recipe
        
        # Define expected filenames based on the new convention: YYYYMMDD_TestDish
        # We assume the test runs on 2026-01-08 as per current context.
        expected_base = "20260108_TestDish"
        expected_illustration = Path(f"/mock/output/recipes/{expected_base}_illustration.png")
        expected_markdown = Path(f"/mock/output/recipes/{expected_base}.md")

        mock_gen_illustration.return_value = expected_illustration
        mock_render_md.return_value = "# Test Recipe"
        mock_write_md.return_value = expected_markdown

        # Act
        results = run_pipeline(mock_config)

        # Assert
        # Verify that all components were called with expected arguments.
        assert len(results) == 1
        assert results[0] == expected_markdown
        
        mock_ensure_dirs.assert_called_once_with(mock_config.output_dir)
        mock_split_to_ratio.assert_called_once()
        mock_build_client.assert_called_once()
        mock_build_image_client.assert_called_once()
        mock_derive_style.assert_called_once()
        
        # Verify that extract_recipe was called with the list of splits
        mock_extract_recipe.assert_called_once_with(
            mock_build_client.return_value, 
            "chat-deploy", 
            mock_split_to_ratio.return_value,
            language="English"
        )
        
        # Verify illustration generation used the image client
        mock_gen_illustration.assert_called_once_with(
            mock_build_image_client.return_value,
            "image-deploy",
            mock_recipe,
            "Watercolor style",
            mock_split_to_ratio.return_value,
            [Path("/mock/style/style1.jpg")],
            expected_illustration
        )
        mock_render_md.assert_called_once_with(mock_recipe, expected_illustration)
        mock_write_md.assert_called_once_with(expected_markdown, "# Test Recipe")


def test_run_pipeline_no_photos(mock_config: AppConfig):
    """Test that run_pipeline raises ValueError when no input photos are found."""
    # Arrange
    with patch("cookbook.pipeline.ensure_output_dirs") as mock_ensure_dirs, \
         patch.object(Path, "glob") as mock_glob:
        
        mock_ensure_dirs.return_value = {"splits": Path("/mock/output/splits")}
        # Simulate NO photos found
        mock_glob.return_value = []

        # Act & Assert
        with pytest.raises(ValueError, match="No photos found in input directory"):
            run_pipeline(mock_config)


def test_run_pipeline_no_styles(mock_config: AppConfig):
    """Test that run_pipeline raises ValueError when no style images are found."""
    # Arrange
    with patch("cookbook.pipeline.ensure_output_dirs"), \
         patch("cookbook.pipeline.split_to_aspect_ratio") as mock_split_to_ratio, \
         patch.object(Path, "glob") as mock_glob:
        
        # First 3 glob calls for photos (find one)
        # Next 2 glob calls for styles (find none)
        mock_glob.side_effect = [
            [Path("/mock/input/photo1.jpg")], [], [], # Photos
            [], [] # Styles
        ]
        mock_split_to_ratio.return_value = [Path("/mock/output/splits/part0.jpg")]

        # Act & Assert
        with pytest.raises(ValueError, match="No reference images found"):
            run_pipeline(mock_config)
