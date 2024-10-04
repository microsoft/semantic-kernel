// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;

namespace Step03.Steps;
public class MockPreparationFoodStep : KernelProcessStep
{
    private readonly string _foodPreparedName = string.Empty;
    private readonly FoodIngredients _ingredientPrepared;
    public static class Functions
    {
        public const string PrepareFood = nameof(PrepareFood);
    }
    public static class OutputEvents
    {
        public const string FoodReady = nameof(FoodReady);
    }

    [KernelFunction(Functions.PrepareFood)]
    public async Task PrepareFoodAsync(KernelProcessStepContext context)
    {
        Console.WriteLine($"PREPARE_FOOD: Food {this._foodPreparedName} Ready!");
        await context.EmitEventAsync(new() { Id = OutputEvents.FoodReady, Data = this._ingredientPrepared });
    }

    public MockPreparationFoodStep(string foodPreparedName, FoodIngredients ingredientPrepared)
    {
        this._foodPreparedName = foodPreparedName;
        this._ingredientPrepared = ingredientPrepared;
    }
}

public class MockPrepareFriedFishStep : MockPreparationFoodStep
{
    public MockPrepareFriedFishStep() : base("Fried Fish Dish", FoodIngredients.Fish) { }
}

public class MockPreparePotatoFriesStep : MockPreparationFoodStep
{
    public MockPreparePotatoFriesStep() : base("Potato Fries Dish", FoodIngredients.Pototoes) { }
}

public class MockPrepareFishSandwichStep : MockPreparationFoodStep
{
    public MockPrepareFishSandwichStep() : base("Fish Sandwich Dish", FoodIngredients.Fish) { }
}
public class MockPrepareFishAndChipsStep : MockPreparationFoodStep
{
    public MockPrepareFishAndChipsStep() : base("Fish & Chips Dish", FoodIngredients.Fish) { }
}
