from __future__ import annotations

from pydantic import BaseModel, Field


class Recipe(BaseModel):
    """Structured recipe data extracted from a photo.

    Attributes:
        dish_name: Name of the dish.
        ingredients: Ingredient list, one item per entry.
        cooking_steps: Ordered cooking steps.
        preparation_time: Preparation time with units.
        tips: Optional cooking tips.
    """

    # Core recipe fields for structured output.
    dish_name: str = Field(..., description="Name of the dish")
    ingredients: list[str] = Field(
        default_factory=list, description="Ingredient list, one item per entry"
    )
    cooking_steps: list[str] = Field(
        default_factory=list, description="Ordered cooking steps"
    )
    preparation_time: str = Field(
        ..., description="Preparation time including units, e.g., '30 minutes'"
    )
    tips: list[str] = Field(default_factory=list, description="Optional cooking tips")
