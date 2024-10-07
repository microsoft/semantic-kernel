// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;
namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with sequential steps and reuse of existing steps.<br/>
/// For a visual reference of the FriedFishProcess check this <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#Fried_Fish_Preparation_Process" >diagram</see>
/// </summary>
public static class FriedFishProcess
{
    public static class ProcessEvents
    {
        public const string PrepareFriedFish = nameof(PrepareFriedFish);
        public const string FriedFishReady = nameof(FriedFishReady);
    }

    public static ProcessBuilder CreateProcess(string processName = "FriedFish")
    {
        var processBuilder = new ProcessBuilder(processName);

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherFriedFishIngredientsStep>();
        var chopStep = processBuilder.AddStepFromType<CutFoodStep>();
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>();
        var externalStep = processBuilder.AddStepFromType<ExternalFriedFishStep>();

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

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FriedFoodReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));

        return processBuilder;
    }

    private sealed class GatherFriedFishIngredientsStep : GatherIngredientsStep
    {
        public override async Task GatherIngredientsAsync(KernelProcessStepContext context, List<string> foodActions)
        {
            var ingredient = FoodIngredients.Fish.ToFriendlyString();

            if (foodActions.Count == 0)
            {
                foodActions.Add(ingredient);
            }
            foodActions.Add($"{ingredient}_gathered");

            Console.WriteLine($"GATHER_INGREDIENT: Gathered ingredient {ingredient}");
            await context.EmitEventAsync(new() { Id = OutputEvents.IngredientsGathered, Data = foodActions });
        }
    }

    private sealed class ExternalFriedFishStep : ExternalStep
    {
        public ExternalFriedFishStep() : base(ProcessEvents.FriedFishReady) { }
    }
}
