# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class FoodItem(str, Enum):
    POTATO_FRIES = "Potato Fries"
    FRIED_FISH = "Fried Fish"
    FISH_SANDWICH = "Fish Sandwich"
    FISH_AND_CHIPS = "Fish & Chips"

    def to_friendly_string(self) -> str:
        return self.value
