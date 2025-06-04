// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
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
        public const string FriedFishReady = FryFoodStep.OutputEvents.FriedFoodReady;
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
        var chopStep = processBuilder.AddStepFromType<CutFoodStep>();
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFriedFish)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsStep.OutputEvents.IngredientsGathered)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodStep.ProcessStepFunctions.ChopFood));

        chopStep
            .OnEvent(CutFoodStep.OutputEvents.ChoppingReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(fryStep));

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FoodRuined)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        return processBuilder;
    }

    public static ProcessBuilder CreateProcessWithStatefulStepsV1(string processName = "FriedFishWithStatefulStepsProcess")
    {
        // It is recommended to specify process version in case this process is used as a step by another process
        var processBuilder = new ProcessBuilder(processName) { Version = "FriedFishProcess.v1" }; ;

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherFriedFishIngredientsWithStockStep>();
        var chopStep = processBuilder.AddStepFromType<CutFoodStep>();
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFriedFish)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsGathered)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.ProcessStepFunctions.ChopFood));

        chopStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.ChoppingReady)
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
    public static ProcessBuilder CreateProcessWithStatefulStepsV2(string processName = "FriedFishWithStatefulStepsProcess")
    {
        // It is recommended to specify process version in case this process is used as a step by another process
        var processBuilder = new ProcessBuilder(processName) { Version = "FriedFishProcess.v2" };

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherFriedFishIngredientsWithStockStep>(id: "gatherFishIngredientStep", aliases: ["GatherFriedFishIngredientsWithStockStep"]);
        var chopStep = processBuilder.AddStepFromType<CutFoodWithSharpeningStep>(id: "chopFishStep", aliases: ["CutFoodStep"]);
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>(id: "fryFishStep", aliases: ["FryFoodStep"]);

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFriedFish)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsGathered)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.ProcessStepFunctions.ChopFood));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock)
            .StopProcess();

        chopStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.ChoppingReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(fryStep));

        chopStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.ProcessStepFunctions.SharpenKnife));

        chopStep
            .OnEvent(CutFoodWithSharpeningStep.OutputEvents.KnifeSharpened)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.ProcessStepFunctions.ChopFood));

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FoodRuined)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        return processBuilder;
    }

    [KernelProcessStepMetadata("GatherFishIngredient.V1")]
    private sealed class GatherFriedFishIngredientsStep : GatherIngredientsStep
    {
        public GatherFriedFishIngredientsStep() : base(FoodIngredients.Fish) { }
    }

    [KernelProcessStepMetadata("GatherFishIngredient.V2")]
    private sealed class GatherFriedFishIngredientsWithStockStep : GatherIngredientsWithStockStep
    {
        public GatherFriedFishIngredientsWithStockStep() : base(FoodIngredients.Fish) { }
    }
}
