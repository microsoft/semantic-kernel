# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class FoodIngredients(str, Enum):
    POTATOES = "Potatoes"
    FISH = "Fish"
    BUNS = "Buns"
    SAUCE = "Sauce"
    CONDIMENTS = "Condiments"
    NONE = "None"

    def to_friendly_string(self) -> str:
        return self.value
