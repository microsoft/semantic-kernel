// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Step03.Models;
using Step03.Steps;
namespace Step03.Processes;

public enum FishProcessEvents
{
    PrepareFriedFish,
    MiddleStep,
    FriedFishFailed,
    FriedFishReady,
}

public class FriedFishEventSubscribers : KernelProcessEventsSubscriber<FishProcessEvents>
{
    // TODO-estenori: figure out how to disallow and not need constructor on when using KernelProcessEventsSubscriber as base class
    public FriedFishEventSubscribers(IServiceProvider? serviceProvider = null) : base(serviceProvider) { }

    [ProcessEventSubscriber(FishProcessEvents.MiddleStep)]
    public void OnMiddleStep(List<string> data)
    {
        // do something with data
        Console.WriteLine($"=============> ON MIDDLE STEP: {data.FirstOrDefault() ?? ""}");
    }

    [ProcessEventSubscriber(FishProcessEvents.FriedFishReady)]
    public void OnPrepareFish(object data)
    {
        // do something with data
        // TODO: if event is linked to last event it doesnt get hit
        // even when it may be linked to StopProcess() -> need additional special step?
        Console.WriteLine("=============> ON FISH READY");
    }

    [ProcessEventSubscriber(FishProcessEvents.FriedFishFailed)]
    public void OnFriedFisFailed(object data)
    {
        // do something with data
        Console.WriteLine("=============> ON FISH FAILED");
    }
}

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
    public static ProcessBuilder<FishProcessEvents> CreateProcess(string processName = "FriedFishProcess")
    {
        var processBuilder = new ProcessBuilder<FishProcessEvents>(processName);

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherFriedFishIngredientsStep>();
        var chopStep = processBuilder.AddStepFromType<CutFoodStep>();
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>();

        processBuilder
            .OnInputEvent(FishProcessEvents.PrepareFriedFish)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsStep.OutputEvents.IngredientsGathered)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(FishProcessEvents.MiddleStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodStep.Functions.ChopFood));

        chopStep
            .OnEvent(CutFoodStep.OutputEvents.ChoppingReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(fryStep));

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FoodRuined)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(FishProcessEvents.FriedFishFailed))
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        fryStep
            .OnEvent(FryFoodStep.OutputEvents.FriedFoodReady)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(FishProcessEvents.FriedFishReady))
            .StopProcess();

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
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.Functions.ChopFood));

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
        var processBuilder = new ProcessBuilder<FishProcessEvents>(processName) { Version = "FriedFishProcess.v2" };

        var gatherIngredientsStep = processBuilder.AddStepFromType<GatherFriedFishIngredientsWithStockStep>(name: "gatherFishIngredientStep", aliases: ["GatherFriedFishIngredientsWithStockStep"]);
        var chopStep = processBuilder.AddStepFromType<CutFoodWithSharpeningStep>(name: "chopFishStep", aliases: ["CutFoodStep"]);
        var fryStep = processBuilder.AddStepFromType<FryFoodStep>(name: "fryFishStep", aliases: ["FryFoodStep"]);

        processBuilder
            .GetProcessEvent(FishProcessEvents.PrepareFriedFish)
            .SendEventTo(new ProcessFunctionTargetBuilder(gatherIngredientsStep));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsGathered)
            .SendEventTo(new ProcessFunctionTargetBuilder(chopStep, functionName: CutFoodWithSharpeningStep.Functions.ChopFood));

        gatherIngredientsStep
            .OnEvent(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(FishProcessEvents.FriedFishFailed))
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

        fryStep.OnEvent(FryFoodStep.OutputEvents.FriedFoodReady)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(FishProcessEvents.FriedFishReady));

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
