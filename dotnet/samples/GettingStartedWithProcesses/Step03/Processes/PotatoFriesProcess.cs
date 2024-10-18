﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with sequential steps and reuse of existing steps.<br/>
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

    /// <summary>
    /// For a visual reference of the PotatoFriesProcess check this
    /// <see href="https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/README.md#potato-fries-preparation-process" >diagram</see>
    /// </summary>
    /// <param name="processName">name of the process</param>
    /// <returns><see cref="ProcessBuilder"/></returns>
    public static ProcessBuilder CreateProcess(string processName = "PotatoFriesProcess")
    {
        var processBuilder = new ProcessBuilder(processName);

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherPotatoFriesIngredientsStep>();
        var sliceStep = processBuilder.AddStepFromType<CutFoodStep>("sliceStep");
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

    /// <summary>
    /// For a visual reference of the PotatoFriesProcess with stateful steps check this
    /// <see href="https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/README.md#potato-fries-preparation-with-knife-sharpening-and-ingredient-stock-process" >diagram</see>
    /// </summary>
    /// <param name="processName">name of the process</param>
    /// <returns><see cref="ProcessBuilder"/></returns>
    public static ProcessBuilder CreateProcessWithStatefulSteps(string processName = "PotatoFriesWithStatefulStepsProcess")
    {
        var processBuilder = new ProcessBuilder(processName);

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherPotatoFriesIngredientsWithStockStep>();
        var sliceStep = processBuilder.AddStepFromType<CutFoodWithSharpeningStep>("sliceStep");
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PreparePotatoFries)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherPotatoFriesIngredientsWithStockStep.OutputEvents.IngredientsGathered)
            .SendEventTo(new ProcessFunctionTargetBuilder(sliceStep, functionName: CutFoodWithSharpeningStep.Functions.SliceFood));

        gatherIngredientsStep
            .OnEvent(GatherPotatoFriesIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock)
            .StopProcess();

        sliceStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.SlicingReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(fryStep));

        sliceStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening)
            .SendEventTo(new ProcessFunctionTargetBuilder(sliceStep, functionName: CutFoodWithSharpeningStep.Functions.SharpenKnife));

        sliceStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.KnifeSharpened)
            .SendEventTo(new ProcessFunctionTargetBuilder(sliceStep, functionName: CutFoodWithSharpeningStep.Functions.SliceFood));

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FoodRuined)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        return processBuilder;
    }

    private sealed class GatherPotatoFriesIngredientsStep : GatherIngredientsStep
    {
        public GatherPotatoFriesIngredientsStep() : base(FoodIngredients.Pototoes) { }
    }

    private sealed class GatherPotatoFriesIngredientsWithStockStep : GatherIngredientsWithStockStep
    {
        public GatherPotatoFriesIngredientsWithStockStep() : base(FoodIngredients.Pototoes) { }
    }
}
