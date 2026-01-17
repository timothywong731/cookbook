from __future__ import annotations

from pydantic import BaseModel, Field


class Recipe(BaseModel):
    """Structured recipe data extracted from a photo.

    Attributes:
        dish_name: Name of the dish.
        description: A short, appetizing description or subtitle for the dish.
        ingredients: Ingredient list, one item per entry.
        cooking_steps: Ordered cooking steps.
        preparation_time: Preparation time with units (e.g., '15 min').
        cooking_time: Cooking time with units (e.g., '30 min').
        servings: Number of servings (e.g., '2').
        tips: Optional cooking tips or notes.
        source_photo: The original filename of the photo from which this recipe was extracted.
    """

    # Core recipe fields for structured output.
    dish_name: str = Field(..., description="Name of the dish")
    description: str = Field(
        "", description="A short, appetizing description or subtitle for the dish"
    )
    ingredients: list[str] = Field(
        default_factory=list, description="Ingredient list, one item per entry"
    )
    cooking_steps: list[str] = Field(
        default_factory=list, description="Ordered cooking steps"
    )
    preparation_time: str = Field(
        "", description="Preparation time including units, e.g., '15 min'"
    )
    cooking_time: str = Field(
        "", description="Cooking time including units, e.g., '30 min'"
    )
    servings: str = Field(
        "", description="Number of servings, e.g., '2'"
    )
    tips: list[str] = Field(default_factory=list, description="Optional cooking tips or notes")
    source_photo: str = Field(
        "", description="The filename of the source photo used for extraction"
    )
    source_photo: str = Field(
        "", description="The filename of the source photo used for extraction"
    )
    source_photo: str = Field(
        "", description="The filename of the source photo used for extraction"
    )
