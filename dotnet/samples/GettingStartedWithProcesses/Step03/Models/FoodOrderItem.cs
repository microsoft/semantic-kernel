// Copyright (c) Microsoft. All rights reserved.

namespace Step03.Models;

/// <summary>
/// Food Items that can be prepared by the PrepareSingleFoodItemProcess
/// </summary>
public enum FoodItem
{
    PotatoFries,
    FriedFish,
    FishSandwich,
    FishAndChips
}

/// <summary>
/// Extensions to have access to friendly string names for <see cref="FoodItem"/>
/// </summary>
public static class FoodItemExtensions
{
    private static readonly Dictionary<FoodItem, string> s_foodItemsStrings = new()
    {
        { FoodItem.PotatoFries, "Potato Fries" },
        { FoodItem.FriedFish, "Fried Fish" },
        { FoodItem.FishSandwich, "Fish Sandwich" },
        { FoodItem.FishAndChips, "Fish & Chips" },
    };

    public static string ToFriendlyString(this FoodItem item)
    {
        return s_foodItemsStrings[item];
    }
}
