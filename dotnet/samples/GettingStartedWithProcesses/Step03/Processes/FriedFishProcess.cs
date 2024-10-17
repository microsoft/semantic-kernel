// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;
namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with sequential steps and reuse of existing steps.<br/>
/// For a visual reference of the FriedFishProcess check this <see href="https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/README.md#fried-fish-preparation-process" >diagram</see>
/// </summary>
public static class FriedFishProcess
{
    public static class ProcessEvents
    {
        public const string PrepareFriedFish = nameof(PrepareFriedFish);
        // When multiple processes use the same final step, the should event marked as public
        // so that the step event can be used as the output event of the process too.
        // In these samples both fried fish and potato fries end with FryStep success
        public const string FriedFishReady = nameof(FryFoodStep.OutputEvents.FriedFoodReady);
    }

    public static ProcessBuilder CreateProcess(string processName = "FriedFishProcess")
    {
        var processBuilder = new ProcessBuilder(processName);

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherFriedFishIngredientsStep>();
        var chopStep = processBuilder.AddStepFromType<CutFoodStep>("chopStep");
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFriedFish)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsStep.OutputEvents.IngredientsGathered)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodStep.Functions.ChopFood));

        chopStep
            .OnEvent(CutFoodStep.OutputEvents.ChoppingReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(fryStep));

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FoodRuined)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        return processBuilder;
    }

    private sealed class GatherFriedFishIngredientsStep : GatherIngredientsStep
    {
        public override async Task GatherIngredientsAsync(KernelProcessStepContext context, List<string> foodActions)
        {
            var ingredient = FoodIngredients.Fish.ToFriendlyString();
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
}
