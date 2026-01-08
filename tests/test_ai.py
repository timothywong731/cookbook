from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import base64
import openai
from openai import AzureOpenAI, OpenAI
from cookbook.ai import (
    _encode_image,
    build_client,
    build_image_client,
    extract_recipe,
    derive_style_prompt,
    generate_illustration,
)
from cookbook.models import Recipe

def test_encode_image(tmp_path: Path):
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake image data")
    encoded = _encode_image(img_path)
    assert encoded == base64.b64encode(b"fake image data").decode("utf-8")

def test_build_client():
    client = build_client("https://test.endpoint", "key", "2023-05-15")
    assert isinstance(client, AzureOpenAI)
    assert client.api_key == "key"

def test_build_image_client_azure():
    client = build_image_client("https://test.endpoint", "key", "2023-05-15")
    assert isinstance(client, AzureOpenAI)

def test_build_image_client_maas():
    client = build_image_client("https://test.models.ai.azure.com", "key", "2023-05-15")
    assert isinstance(client, OpenAI)
    assert client.base_url == "https://test.models.ai.azure.com/v1/"

def test_extract_recipe():
    mock_client = MagicMock(spec=AzureOpenAI)
    mock_response = MagicMock()
    mock_recipe = Recipe(dish_name="Test", ingredients=[], cooking_steps=[], preparation_time="10m")
    mock_response.choices[0].message.parsed = mock_recipe
    mock_client.beta.chat.completions.parse.return_value = mock_response
    
    recipe = extract_recipe(mock_client, "deploy", [Path("tests/test_ai.py")])
    assert recipe == mock_recipe

def test_extract_recipe_none():
    mock_client = MagicMock(spec=AzureOpenAI)
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = None
    mock_client.beta.chat.completions.parse.return_value = mock_response
    
    with pytest.raises(ValueError, match="Azure OpenAI failed to return a valid recipe structure."):
        extract_recipe(mock_client, "deploy", [Path("tests/test_ai.py")])

def test_derive_style_prompt():
    mock_client = MagicMock(spec=AzureOpenAI)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = " Watercolor style "
    mock_client.chat.completions.create.return_value = mock_response
    
    style = derive_style_prompt(mock_client, "deploy", [Path("tests/test_ai.py")])
    assert style == "Watercolor style"

def test_derive_style_prompt_none():
    mock_client = MagicMock(spec=AzureOpenAI)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = None
    mock_client.chat.completions.create.return_value = mock_response
    
    with pytest.raises(ValueError, match="No style prompt returned from Azure OpenAI."):
        derive_style_prompt(mock_client, "deploy", [Path("tests/test_ai.py")])

def test_generate_illustration_success(tmp_path):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data[0].b64_json = base64.b64encode(b"fake image response").decode("utf-8")
    mock_client.images.generate.return_value = mock_response
    
    recipe = Recipe(dish_name="Test", ingredients=["ing1"], cooking_steps=[], preparation_time="10m")
    output_path = tmp_path / "output.png"
    
    with patch("cookbook.ai._encode_image", return_value="encoded"):
        result = generate_illustration(mock_client, "deploy", recipe, "style", [], [], output_path)
    
    assert result == output_path
    assert output_path.read_bytes() == b"fake image response"

def test_generate_illustration_retry_on_block(tmp_path):
    mock_client = MagicMock()
    
    # First call fails with blocklist error
    # Second call succeeds
    mock_response = MagicMock()
    mock_response.data[0].b64_json = base64.b64encode(b"retry success").decode("utf-8")
    
    mock_client.images.generate.side_effect = [
        openai.BadRequestError("Bing blocklist triggered", response=MagicMock(), body={}),
        mock_response
    ]
    
    recipe = Recipe(dish_name="Test", ingredients=["ing1"], cooking_steps=[], preparation_time="10m")
    output_path = tmp_path / "output_retry.png"
    
    with patch("cookbook.ai._encode_image", return_value="encoded"):
        result = generate_illustration(mock_client, "deploy", recipe, "style", [], [], output_path)
    
    assert result == output_path
    assert output_path.read_bytes() == b"retry success"
    assert mock_client.images.generate.call_count == 2

def test_generate_illustration_double_retry_on_block(tmp_path):
    mock_client = MagicMock()
    
    # First and second calls fail with blocklist error
    # Third call succeeds
    mock_response = MagicMock()
    mock_response.data[0].b64_json = base64.b64encode(b"double retry success").decode("utf-8")
    
    mock_client.images.generate.side_effect = [
        openai.BadRequestError("Content blocked", response=MagicMock(), body={}),
        openai.BadRequestError("Content blocked", response=MagicMock(), body={}),
        mock_response
    ]
    
    recipe = Recipe(dish_name="Test", ingredients=["ing1"], cooking_steps=[], preparation_time="10m")
    output_path = tmp_path / "output_double_retry.png"
    
    with patch("cookbook.ai._encode_image", return_value="encoded"):
        result = generate_illustration(mock_client, "deploy", recipe, "style", [], [], output_path)
    
    assert result == output_path
    assert output_path.read_bytes() == b"double retry success"
    assert mock_client.images.generate.call_count == 3

def test_generate_illustration_unhandled_error(tmp_path):
    mock_client = MagicMock()
    mock_client.images.generate.side_effect = Exception("Unhandled")
    
    recipe = Recipe(dish_name="Test", ingredients=["ing1"], cooking_steps=[], preparation_time="10m")
    output_path = tmp_path / "output_error.png"
    
    with patch("cookbook.ai._encode_image", return_value="encoded"):
        with pytest.raises(Exception, match="Unhandled"):
            generate_illustration(mock_client, "deploy", recipe, "style", [], [], output_path)

def test_generate_illustration_unhandled_bad_request(tmp_path):
    mock_client = MagicMock()
    # BadRequestError without "blocklist" or "content" in the message
    mock_client.images.generate.side_effect = openai.BadRequestError("Something else", response=MagicMock(), body={})
    
    recipe = Recipe(dish_name="Test", ingredients=["ing1"], cooking_steps=[], preparation_time="10m")
    output_path = tmp_path / "output_bad_request.png"
    
    with patch("cookbook.ai._encode_image", return_value="encoded"):
        with pytest.raises(openai.BadRequestError, match="Something else"):
            generate_illustration(mock_client, "deploy", recipe, "style", [], [], output_path)
