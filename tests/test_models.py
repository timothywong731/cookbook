from cookbook.models import Recipe


def test_recipe_model_accepts_required_fields() -> None:
    """Validate that the Recipe model accepts required fields and the new source_photo field."""

    # Arrange
    required_data = {
        "dish_name": "Noodle Soup",
        "ingredients": ["noodles", "broth"],
        "cooking_steps": ["Boil", "Serve"],
        "preparation_time": "15 minutes",
        "tips": ["Add herbs"],
        "source_photo": "img_01.jpg",
    }

    # Act
    recipe = Recipe(**required_data)

    # Assert
    assert recipe.dish_name == "Noodle Soup"
    assert recipe.source_photo == "img_01.jpg"
