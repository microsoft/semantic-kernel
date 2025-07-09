// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;

namespace Step03.Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_03_FoodPreparation.cs
/// </summary>
[KernelProcessStepMetadata("CutFoodStep.V1")]
public class CutFoodStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string ChopFood = nameof(ChopFood);
        public const string SliceFood = nameof(SliceFood);
    }

    public static new class StepEvents
    {
        public static readonly KernelProcessEventDescriptor<List<string>> ChoppingReady = new(nameof(ChoppingReady));
        public static readonly KernelProcessEventDescriptor<List<string>> SlicingReady = new(nameof(SlicingReady));
    }

    [KernelFunction(ProcessStepFunctions.ChopFood)]
    public async Task ChopFoodAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        var foodToBeCut = foodActions.First();
        foodActions.Add(this.getActionString(foodToBeCut, "chopped"));
        Console.WriteLine($"CUTTING_STEP: Ingredient {foodToBeCut} has been chopped!");
        await context.EmitEventAsync(StepEvents.ChoppingReady, foodActions);
    }

    [KernelFunction(ProcessStepFunctions.SliceFood)]
    public async Task SliceFoodAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        var foodToBeCut = foodActions.First();
        foodActions.Add(this.getActionString(foodToBeCut, "sliced"));
        Console.WriteLine($"CUTTING_STEP: Ingredient {foodToBeCut} has been sliced!");
        await context.EmitEventAsync(StepEvents.SlicingReady, foodActions);
    }

    private string getActionString(string food, string action)
    {
        return $"{food}_{action}";
    }
}
