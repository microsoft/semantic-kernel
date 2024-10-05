// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;

namespace Step03.Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_03_FoodPreparation.cs
/// </summary>
public class CutFoodStep : KernelProcessStep
{
    public static class Functions
    {
        public const string ChopFood = nameof(ChopFood);
        public const string SliceFood = nameof(SliceFood);
    }

    public static class OutputEvents
    {
        public const string ChoppingReady = nameof(ChoppingReady);
        public const string SlicingReady = nameof(SlicingReady);
    }

    [KernelFunction(Functions.ChopFood)]
    public async Task ChopFoodAsync(KernelProcessStepContext context, FoodIngredients foodToBeCut)
    {
        Console.WriteLine($"CUTTING_STEP: Ingredient {foodToBeCut.ToFriendlyString()} has been chopped!");
        await context.EmitEventAsync(new() { Id = OutputEvents.ChoppingReady, Data = foodToBeCut });
    }

    [KernelFunction(Functions.SliceFood)]
    public async Task SliceFoodAsync(KernelProcessStepContext context, FoodIngredients foodToBeCut)
    {
        Console.WriteLine($"CUTTING_STEP: Ingredient {foodToBeCut.ToFriendlyString()} has been sliced!");
        await context.EmitEventAsync(new() { Id = OutputEvents.SlicingReady, Data = foodToBeCut });
    }
}
