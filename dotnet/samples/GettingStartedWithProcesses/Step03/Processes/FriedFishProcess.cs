﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;
namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with sequential steps and reuse of existing steps.<br/>
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

    /// <summary>
    /// For a visual reference of the FriedFishProcess check this
    /// <see href="https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/README.md#fried-fish-preparation-process" >diagram</see>
    /// </summary>
    /// <param name="processName">name of the process</param>
    /// <returns><see cref="ProcessBuilder"/></returns>
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

    /// <summary>
    /// For a visual reference of the FriedFishProcess with stateful steps check this
    /// <see href="https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/README.md#fried-fish-preparation-with-knife-sharpening-and-ingredient-stock-process" >diagram</see>
    /// </summary>
    /// <param name="processName">name of the process</param>
    /// <returns><see cref="ProcessBuilder"/></returns>
    public static ProcessBuilder CreateProcessWithStatefulSteps(string processName = "FriedFishWithStatefulStepsProcess")
    {
        var processBuilder = new ProcessBuilder(processName);

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherFriedFishIngredientsWithStockStep>();
        var chopStep = processBuilder.AddStepFromType<CutFoodWithSharpeningStep>("chopStep");
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFriedFish)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsGathered)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.Functions.ChopFood));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock)
            .StopProcess();

        chopStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.ChoppingReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(fryStep));

        chopStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.Functions.SharpenKnife));

        chopStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.KnifeSharpened)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.Functions.ChopFood));

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FoodRuined)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        return processBuilder;
    }

    private sealed class GatherFriedFishIngredientsStep : GatherIngredientsStep
    {
        public GatherFriedFishIngredientsStep() : base(FoodIngredients.Fish) { }
    }

    private sealed class GatherFriedFishIngredientsWithStockStep : GatherIngredientsWithStockStep
    {
        public GatherFriedFishIngredientsWithStockStep() : base(FoodIngredients.Fish) { }
    }
}
