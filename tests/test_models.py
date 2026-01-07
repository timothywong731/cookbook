from cookbook.models import Recipe


def test_recipe_model_accepts_required_fields() -> None:
    """Validate that the Recipe model accepts required fields."""

    # Create a valid Recipe instance.
    recipe = Recipe(
        dish_name="Noodle Soup",
        ingredients=["noodles", "broth"],
        cooking_steps=["Boil", "Serve"],
        preparation_time="15 minutes",
        tips=["Add herbs"],
    )

    assert recipe.dish_name == "Noodle Soup"
