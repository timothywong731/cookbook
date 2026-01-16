from __future__ import annotations

import argparse
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cookbook.config import AppConfig
from cookbook.main import _get_env, build_config, main


def test_get_env_success():
    """Test _get_env returns the value when the environment variable exists."""
    # Arrange
    name = "TEST_VAR"
    expected_value = "test-value"
    with patch.dict(os.environ, {name: expected_value}):
        # Act
        result = _get_env(name)

        # Assert
        assert result == expected_value


def test_get_env_failure():
    """Test _get_env raises ValueError when the environment variable is missing."""
    # Arrange
    name = "MISSING_VAR"
    with patch.dict(os.environ, {}, clear=True):
        # Act & Assert
        with pytest.raises(ValueError, match=f"Missing required environment variable: {name}"):
            _get_env(name)


def test_build_config():
    """Test build_config correctly combines CLI args and environment variables."""
    # Arrange
    args = argparse.Namespace(
        input_dir="input_test",
        output_dir="output_test",
        aspect_ratio=1.0,
        split_margin_ratio=0.2,
        reference_style_dir="style_test",
        language="French",
        export_html=True,
    )
    
    mock_env = {
        "AZURE_OPENAI_ENDPOINT": "https://endpoint",
        "AZURE_OPENAI_API_KEY": "key",
        "AZURE_OPENAI_API_VERSION": "2023-05-15",
        "AZURE_OPENAI_CHAT_DEPLOYMENT": "chat-deploy",
        "AZURE_OPENAI_IMAGE_DEPLOYMENT": "image-deploy",
    }
    
    with patch.dict(os.environ, mock_env):
        # Act
        config = build_config(args)

        # Assert
        assert isinstance(config, AppConfig)
        assert config.input_dir == Path("input_test")
        assert config.output_dir == Path("output_test")
        assert config.aspect_ratio == 1.0
        assert config.split_margin_ratio == 0.2
        assert config.azure_openai_endpoint == "https://endpoint"
        assert config.language == "French"
        assert config.export_html is True


def test_main_execution():
    """Test the main entry point parses arguments and runs the pipeline."""
    # Arrange
    with patch("cookbook.main.argparse.ArgumentParser.parse_args") as mock_parse, \
         patch("cookbook.main.build_config") as mock_build_config, \
         patch("cookbook.main.run_pipeline") as mock_run_pipeline, \
         patch("builtins.print") as mock_print:
        
        mock_parse.return_value = argparse.Namespace()
        mock_config = MagicMock(spec=AppConfig)
        mock_build_config.return_value = mock_config
        mock_run_pipeline.return_value = [Path("output/recipe1.json")]

        # Act
        main()

        # Assert
        mock_parse.assert_called_once()
        mock_build_config.assert_called_once()
        mock_run_pipeline.assert_called_once_with(mock_config)
        
        # Windows vs POSIX path separator in print
        expected_output = f"Generated {Path('output/recipe1.json')}"
        mock_print.assert_called_with(expected_output)
