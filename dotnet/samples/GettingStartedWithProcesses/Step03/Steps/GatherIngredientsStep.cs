// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
namespace Step03.Steps;

/// <summary>
/// Step used as base by many other cooking processes
/// When used in other processes a new step is based on this one with custom GatherIngredientsAsync functionality
/// </summary>
public class GatherIngredientsStep : KernelProcessStep
{
    public static class Functions
    {
        public const string GatherIngredients = nameof(GatherIngredients);
    }

    public static class OutputEvents
    {
        public const string IngredientsGathered = nameof(IngredientsGathered);
    }

    /// <summary>
    /// Method to be overridden by the user set custom ingredients to be gathered and events to be triggered
    /// </summary>
    /// <param name="context"></param>
    /// <returns></returns>
    [KernelFunction(Functions.GatherIngredients)]
    public virtual async Task GatherIngredientsAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        await context.EmitEventAsync(new() { Id = OutputEvents.IngredientsGathered, Data = foodActions });
    }
}
