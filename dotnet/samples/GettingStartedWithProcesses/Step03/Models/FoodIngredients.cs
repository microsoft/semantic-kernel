// Copyright (c) Microsoft. All rights reserved.

namespace Step03.Models;

/// <summary>
/// Food Ingredients used in steps such GatherIngredientStep, CutFoodStep, FryFoodStep
/// </summary>
public enum FoodIngredients
{
    Pototoes,
    Fish,
    Buns,
    Sauce,
    Condiments,
    None
}

/// <summary>
/// Extensions to have access to friendly string names for <see cref="FoodIngredients"/>
/// </summary>
public static class FoodIngredientsExtensions
{
    private static readonly Dictionary<FoodIngredients, string> s_foodIngredientsStrings = new()
    {
        { FoodIngredients.Pototoes, "Potatoes" },
        { FoodIngredients.Fish, "Fish" },
        { FoodIngredients.Buns, "Buns" },
        { FoodIngredients.Sauce, "Sauce" },
        { FoodIngredients.Condiments, "Condiments" },
        { FoodIngredients.None, "None" }
    };

    public static string ToFriendlyString(this FoodIngredients ingredient)
    {
        return s_foodIngredientsStrings[ingredient];
    }
}
