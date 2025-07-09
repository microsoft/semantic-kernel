// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;

namespace Step03.Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_03_FoodPreparation.cs
/// </summary>
[KernelProcessStepMetadata("FryFoodStep.V1")]
public class FryFoodStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string FryFood = nameof(FryFood);
    }

    public static new class StepEvents
    {
        public static readonly KernelProcessEventDescriptor<List<string>> FoodRuined = new(nameof(FoodRuined));
        public static readonly KernelProcessEventDescriptor<List<string>> FriedFoodReady = new(nameof(FriedFoodReady));
    }

    private readonly Random _randomSeed = new();

    [KernelFunction(ProcessStepFunctions.FryFood)]
    public async Task FryFoodAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        var foodToFry = foodActions.First();
        // This step may fail sometimes
        int fryerMalfunction = _randomSeed.Next(0, 10);

        // foodToFry could potentially be used to set the frying temperature and cooking duration
        if (fryerMalfunction < 5)
        {
            // Oh no! Food got burnt :(
            foodActions.Add($"{foodToFry}_frying_failed");
            Console.WriteLine($"FRYING_STEP: Ingredient {foodToFry} got burnt while frying :(");
            await context.EmitEventAsync(StepEvents.FoodRuined, foodActions);
            return;
        }

        foodActions.Add($"{foodToFry}_frying_succeeded");
        Console.WriteLine($"FRYING_STEP: Ingredient {foodToFry} is ready!");
        await context.EmitEventAsync(StepEvents.FriedFoodReady, foodActions);
    }
}
