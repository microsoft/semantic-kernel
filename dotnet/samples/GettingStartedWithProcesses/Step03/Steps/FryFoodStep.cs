﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step03.Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_03_FoodPreparation.cs
/// </summary>
public class FryFoodStep : KernelProcessStep
{
    public static class Functions
    {
        public const string FryFood = nameof(FryFood);
    }

    public static class OutputEvents
    {
        public const string FoodRuined = nameof(FoodRuined);
        public const string FriedFoodReady = nameof(FriedFoodReady);
    }

    private readonly Random _randomSeed = new();

    [KernelFunction(Functions.FryFood)]
    public async Task FryFoodAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        var foodToFry = foodActions.First();
        // This step may fail sometimes
        int fryerMalfunction = _randomSeed.Next(0, 10);

        // foodToFry could potentially be used to set the frying temperature and cooking duration
        if (fryerMalfunction > 6)
        {
            // Oh no! Food got burnt :(
            foodActions.Add($"{foodToFry}_frying_failed");
            Console.WriteLine($"FRYING_STEP: Ingredient {foodToFry} got burnt while frying :(");
            await context.EmitEventAsync(new() { Id = OutputEvents.FoodRuined, Data = foodActions });
            return;
        }

        foodActions.Add($"{foodToFry}_frying_succeeded");
        Console.WriteLine($"FRYING_STEP: Ingredient {foodToFry} is ready!");
        await context.EmitEventAsync(new() { Id = OutputEvents.FriedFoodReady, Data = foodActions, Visibility = KernelProcessEventVisibility.Public });
    }
}
