﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with sequential steps and reuse of existing steps.<br/>
/// For a visual reference of the FriedFishProcess check this <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#Potato_Fries_Preparation_Process" >diagram</see>
/// </summary>
public static class PotatoFriesProcess
{
    public static class ProcessEvents
    {
        public const string PreparePotatoFries = nameof(PreparePotatoFries);
        // When multiple processes use the same final step, the should event marked as public
        // so that the step event can be used as the output event of the process too.
        // In these samples both fried fish and potato fries end with FryStep success
        public const string PotatoFriesReady = nameof(FryFoodStep.OutputEvents.FriedFoodReady);
    }

    public static ProcessBuilder CreateProcess(string processName = "PotatoFriesProcess")
    {
        var processBuilder = new ProcessBuilder(processName);

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherPotatoFriesIngredientsStep>();
        var sliceStep = processBuilder.AddStepFromType<CutFoodStep>();
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>();

        processBuilder
                .OnInputEvent(ProcessEvents.PreparePotatoFries)
                .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherPotatoFriesIngredientsStep.OutputEvents.IngredientsGathered)
            .SendEventTo(new ProcessFunctionTargetBuilder(sliceStep, functionName: CutFoodStep.Functions.SliceFood));

        sliceStep
            .OnEvent(CutFoodStep.OutputEvents.SlicingReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(fryStep));

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FoodRuined)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        return processBuilder;
    }

    private sealed class GatherPotatoFriesIngredientsStep : GatherIngredientsStep
    {
        public override async Task GatherIngredientsAsync(KernelProcessStepContext context, List<string> foodActions)
        {
            var ingredient = FoodIngredients.Pototoes.ToFriendlyString();
            var updatedFoodActions = new List<string>();
            updatedFoodActions.AddRange(foodActions);
            if (updatedFoodActions.Count == 0)
            {
                updatedFoodActions.Add(ingredient);
            }
            updatedFoodActions.Add($"{ingredient}_gathered");

            Console.WriteLine($"GATHER_INGREDIENT: Gathered ingredient {ingredient}");
            await context.EmitEventAsync(new() { Id = OutputEvents.IngredientsGathered, Data = updatedFoodActions });
        }
    }

    private sealed class ExternalPotatoFriesStep : ExternalStep
    {
        public ExternalPotatoFriesStep() : base(ProcessEvents.PotatoFriesReady) { }
    }
}
