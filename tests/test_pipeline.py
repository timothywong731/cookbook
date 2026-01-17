from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import openai
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
        export_html=True,
    )


def _glob_side_effect(
    input_dir: Path,
    recipes_dir: Path,
    style_dir: Path,
    input_files: list[Path],
    json_files: list[Path],
    style_files: list[Path],
) -> callable:
    def _side_effect(self: Path, pattern: str) -> list[Path]:
        if self == input_dir:
            if pattern == "*.jpg":
                return input_files
            if pattern in {"*.jpeg", "*.png"}:
                return []
        if self == recipes_dir and pattern == "*.json":
            return json_files
        if self == style_dir:
            if pattern == "*.jpg":
                return style_files
            if pattern == "*.png":
                return []
        return []

    return _side_effect


def test_run_pipeline_success(mock_config: AppConfig) -> None:
    """Test that run_pipeline executes all steps correctly under normal conditions."""
    # Arrange
    recipes_dir = Path("/mock/output/recipes")
    splits_dir = Path("/mock/output/splits")
    input_file = Path("/mock/input/recipe1.jpg")
    style_file = Path("/mock/style/style1.jpg")

    with patch("cookbook.pipeline.ensure_output_dirs") as mock_ensure_dirs, \
         patch("cookbook.pipeline.split_to_aspect_ratio") as mock_split_to_ratio, \
         patch("cookbook.pipeline.build_client") as mock_build_client, \
         patch("cookbook.pipeline.build_image_client") as mock_build_image_client, \
         patch("cookbook.pipeline.derive_style_prompt") as mock_derive_style, \
         patch("cookbook.pipeline.extract_recipe") as mock_extract_recipe, \
         patch("cookbook.pipeline.generate_illustration") as mock_gen_illustration, \
         patch("cookbook.pipeline.render_recipe_html") as mock_render_html, \
         patch("cookbook.pipeline.write_recipe_html") as mock_write_html, \
         patch("cookbook.pipeline.rebuild_index") as mock_rebuild_index, \
         patch.object(Path, "write_text") as mock_write_text, \
         patch.object(Path, "glob", autospec=True) as mock_glob, \
         patch("datetime.datetime") as mock_date:

        mock_ensure_dirs.return_value = {"splits": splits_dir, "recipes": recipes_dir}

        mock_glob.side_effect = _glob_side_effect(
            input_dir=mock_config.input_dir,
            recipes_dir=recipes_dir,
            style_dir=mock_config.reference_style_dir,
            input_files=[input_file],
            json_files=[],
            style_files=[style_file],
        )

        mock_split_to_ratio.return_value = [Path("/mock/output/splits/recipe1_part0.jpg")]
        mock_build_client.return_value = MagicMock()
        mock_build_image_client.return_value = MagicMock()
        mock_derive_style.return_value = "Watercolor style"

        mock_recipe = Recipe(
            dish_name="Test Dish",
            ingredients=["ing1"],
            cooking_steps=["step1"],
            preparation_time="10 mins",
        )
        mock_extract_recipe.return_value = mock_recipe

        mock_date.now.return_value.strftime.return_value = "20260116"
        expected_base = "20260116_TestDish"
        expected_illustration = recipes_dir / f"{expected_base}_illustration.png"
        expected_json = recipes_dir / f"{expected_base}.json"
        expected_html = recipes_dir / f"{expected_base}.html"

        mock_gen_illustration.return_value = expected_illustration
        mock_render_html.return_value = "<html>Test Recipe</html>"

        # Act
        results = run_pipeline(mock_config)

        # Assert
        assert results == [expected_json, expected_html]
        assert mock_recipe.source_photo == "recipe1.jpg"
        mock_split_to_ratio.assert_called_once()
        mock_extract_recipe.assert_called_once_with(
            mock_build_client.return_value,
            "chat-deploy",
            mock_split_to_ratio.return_value,
            language="English",
        )
        mock_gen_illustration.assert_called_once_with(
            mock_build_image_client.return_value,
            "image-deploy",
            mock_recipe,
            "Watercolor style",
            mock_split_to_ratio.return_value,
            [style_file],
            expected_illustration,
        )
        mock_write_text.assert_called_once()
        mock_write_html.assert_called_once_with(expected_html, "<html>Test Recipe</html>")
        mock_rebuild_index.assert_called_once_with(recipes_dir)


def test_run_pipeline_skips_processed(mock_config: AppConfig) -> None:
    """Test that run_pipeline skips photos that have already been processed."""
    # Arrange
    recipes_dir = Path("/mock/output/recipes")
    splits_dir = Path("/mock/output/splits")
    input_file = Path("/mock/input/recipe1.jpg")
    json_file = recipes_dir / "old_recipe.json"

    with patch("cookbook.pipeline.ensure_output_dirs") as mock_ensure_dirs, \
         patch("cookbook.pipeline.build_client") as mock_build_client, \
         patch("cookbook.pipeline.derive_style_prompt") as mock_derive_style, \
         patch.object(Path, "glob", autospec=True) as mock_glob, \
         patch.object(Path, "read_text") as mock_read_text:

        mock_ensure_dirs.return_value = {"splits": splits_dir, "recipes": recipes_dir}

        mock_glob.side_effect = _glob_side_effect(
            input_dir=mock_config.input_dir,
            recipes_dir=recipes_dir,
            style_dir=mock_config.reference_style_dir,
            input_files=[input_file],
            json_files=[json_file],
            style_files=[],
        )

        mock_read_text.return_value = json.dumps({"source_photo": "recipe1.jpg"})

        # Act
        results = run_pipeline(mock_config)

        # Assert
        assert results == []
        mock_build_client.assert_not_called()
        mock_derive_style.assert_not_called()


def test_run_pipeline_handles_content_filter_error(mock_config: AppConfig) -> None:
    """Test that run_pipeline handles Azure OpenAI content filter violations."""
    # Arrange
    recipes_dir = Path("/mock/output/recipes")
    splits_dir = Path("/mock/output/splits")
    input_file = Path("/mock/input/bad_photo.jpg")
    style_file = Path("/mock/style/style1.jpg")

    with patch("cookbook.pipeline.ensure_output_dirs") as mock_ensure_dirs, \
         patch("cookbook.pipeline.split_to_aspect_ratio") as mock_split_to_ratio, \
         patch("cookbook.pipeline.build_client"), \
         patch("cookbook.pipeline.build_image_client"), \
         patch("cookbook.pipeline.derive_style_prompt"), \
         patch("cookbook.pipeline.extract_recipe") as mock_extract_recipe, \
         patch("cookbook.pipeline.rebuild_index") as mock_rebuild_index, \
         patch.object(Path, "glob", autospec=True) as mock_glob:

        mock_ensure_dirs.return_value = {"splits": splits_dir, "recipes": recipes_dir}

        mock_glob.side_effect = _glob_side_effect(
            input_dir=mock_config.input_dir,
            recipes_dir=recipes_dir,
            style_dir=mock_config.reference_style_dir,
            input_files=[input_file],
            json_files=[],
            style_files=[style_file],
        )

        mock_split_to_ratio.return_value = [Path("/mock/output/splits/bad_part0.jpg")]
        mock_extract_recipe.side_effect = openai.BadRequestError(
            message="The response was filtered due to the prompt triggering Azure OpenAI's content management policy.",
            response=MagicMock(),
            body={"error": {"code": "content_filter"}},
        )

        # Act
        results = run_pipeline(mock_config)

        # Assert
        assert results == []
        mock_extract_recipe.assert_called_once()
        mock_rebuild_index.assert_called_once_with(recipes_dir)


def test_run_pipeline_no_photos(mock_config: AppConfig) -> None:
    """Test that run_pipeline returns empty output when no input photos are found."""
    # Arrange
    recipes_dir = Path("/mock/output/recipes")
    splits_dir = Path("/mock/output/splits")

    with patch("cookbook.pipeline.ensure_output_dirs") as mock_ensure_dirs, \
         patch("cookbook.pipeline.build_client") as mock_build_client, \
         patch.object(Path, "glob", autospec=True) as mock_glob:

        mock_ensure_dirs.return_value = {"splits": splits_dir, "recipes": recipes_dir}

        mock_glob.side_effect = _glob_side_effect(
            input_dir=mock_config.input_dir,
            recipes_dir=recipes_dir,
            style_dir=mock_config.reference_style_dir,
            input_files=[],
            json_files=[],
            style_files=[],
        )

        # Act
        results = run_pipeline(mock_config)

        # Assert
        assert results == []
        mock_build_client.assert_not_called()


def test_run_pipeline_no_styles(mock_config: AppConfig) -> None:
    """Test that run_pipeline raises ValueError when no style images are found."""
    # Arrange
    recipes_dir = Path("/mock/output/recipes")
    splits_dir = Path("/mock/output/splits")
    input_file = Path("/mock/input/photo1.jpg")

    with patch("cookbook.pipeline.ensure_output_dirs") as mock_ensure_dirs, \
         patch("cookbook.pipeline.split_to_aspect_ratio") as mock_split_to_ratio, \
         patch.object(Path, "glob", autospec=True) as mock_glob:

        mock_ensure_dirs.return_value = {"splits": splits_dir, "recipes": recipes_dir}

        mock_glob.side_effect = _glob_side_effect(
            input_dir=mock_config.input_dir,
            recipes_dir=recipes_dir,
            style_dir=mock_config.reference_style_dir,
            input_files=[input_file],
            json_files=[],
            style_files=[],
        )

        mock_split_to_ratio.return_value = [Path("/mock/output/splits/part0.jpg")]

        # Act & Assert
        with pytest.raises(ValueError, match="No reference images found"):
            run_pipeline(mock_config)
