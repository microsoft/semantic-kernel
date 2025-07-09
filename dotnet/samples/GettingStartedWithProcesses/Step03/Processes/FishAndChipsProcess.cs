// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with a fan in/fan out behavior and use of existing processes as steps.<br/>
/// Visual reference of this process can be found in the <see href="https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/README.md#fish-and-chips-preparation-process" >diagram</see>
/// </summary>
public static class FishAndChipsProcess
{
    public static class ProcessEvents
    {
        public const string PrepareFishAndChips = nameof(PrepareFishAndChips);
        public const string FishAndChipsReady = nameof(FishAndChipsReady);
        public const string FishAndChipsIngredientOutOfStock = nameof(FishAndChipsIngredientOutOfStock);
    }

    public static ProcessBuilder CreateProcess(string processName = "FishAndChipsProcess")
    {
        var processBuilder = new ProcessBuilder(processName);
        var makeFriedFishStep = processBuilder.AddStepFromProcess(FriedFishProcess.CreateProcess());
        var makePotatoFriesStep = processBuilder.AddStepFromProcess(PotatoFriesProcess.CreateProcess());
        var addCondimentsStep = processBuilder.AddStepFromType<AddFishAndChipsCondimentsStep>();
        // An additional step that is the only one that emits an public event in a process can be added to maintain event names unique
        var externalStep = processBuilder.AddStepFromType<ExternalFishAndChipsStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFishAndChips)
            .SendEventTo(makeFriedFishStep.WhereInputEventIs(FriedFishProcess.ProcessEvents.PrepareFriedFish))
            .SendEventTo(makePotatoFriesStep.WhereInputEventIs(PotatoFriesProcess.ProcessEvents.PreparePotatoFries));

        processBuilder.ListenFor().AllOf([
            new(FriedFishProcess.ProcessEvents.FriedFishReady, makeFriedFishStep),
            new(PotatoFriesProcess.ProcessEvents.PotatoFriesReady, makePotatoFriesStep),
        ]).SendEventTo(new ProcessStepTargetBuilder(addCondimentsStep, inputMapping: inputEvents =>
        {
            return new() {
                { "fishActions", inputEvents[makeFriedFishStep.GetFullEventId(FriedFishProcess.ProcessEvents.FriedFishReady)] },
                { "potatoActions", inputEvents[makePotatoFriesStep.GetFullEventId(PotatoFriesProcess.ProcessEvents.PotatoFriesReady)] },
            };
        }));

        addCondimentsStep
            .OnEvent(AddFishAndChipsCondimentsStep.StepEvents.CondimentsAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));

        externalStep.OnEvent(ExternalFishAndChipsStep.StepEvents.FishAndChipsReady).EmitAsPublicEvent();

        return processBuilder;
    }

    public static ProcessBuilder CreateProcessWithStatefulSteps(string processName = "FishAndChipsWithStatefulStepsProcess")
    {
        var processBuilder = new ProcessBuilder(processName);
        var makeFriedFishStep = processBuilder.AddStepFromProcess(FriedFishProcess.CreateProcessWithStatefulStepsV1());
        var makePotatoFriesStep = processBuilder.AddStepFromProcess(PotatoFriesProcess.CreateProcessWithStatefulSteps());
        var addCondimentsStep = processBuilder.AddStepFromType<AddFishAndChipsCondimentsStep>();
        // An additional step that is the only one that emits an public event in a process can be added to maintain event names unique
        var externalStep = processBuilder.AddStepFromType<ExternalFishAndChipsStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFishAndChips)
            .SendEventTo(makeFriedFishStep.WhereInputEventIs(FriedFishProcess.ProcessEvents.PrepareFriedFish))
            .SendEventTo(makePotatoFriesStep.WhereInputEventIs(PotatoFriesProcess.ProcessEvents.PreparePotatoFries));

        processBuilder.ListenFor().AllOf(
            [
                new(FriedFishProcess.ProcessEvents.FriedFishReady, makeFriedFishStep),
                new(PotatoFriesProcess.ProcessEvents.PotatoFriesReady, makePotatoFriesStep),
            ]).SendEventTo(new ProcessStepTargetBuilder(addCondimentsStep, inputMapping: inputEvents =>
            {
                return new() {
                    { "fishActions", inputEvents[makeFriedFishStep.GetFullEventId(FriedFishProcess.ProcessEvents.FriedFishReady)] },
                    { "potatoActions", inputEvents[makePotatoFriesStep.GetFullEventId(PotatoFriesProcess.ProcessEvents.PotatoFriesReady)] },
                };
            }));

        addCondimentsStep
            .OnEvent(AddFishAndChipsCondimentsStep.StepEvents.CondimentsAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));

        externalStep.OnEvent(ExternalFishAndChipsStep.StepEvents.FishAndChipsReady).EmitAsPublicEvent();

        return processBuilder;
    }

    private sealed class AddFishAndChipsCondimentsStep : KernelProcessStep
    {
        public static class ProcessFunctions
        {
            public const string AddCondiments = nameof(AddCondiments);
        }

        public static new class StepEvents
        {
            public static readonly KernelProcessEventDescriptor<List<string>> CondimentsAdded = new(nameof(CondimentsAdded));
        }

        [KernelFunction(ProcessFunctions.AddCondiments)]
        public async Task AddCondimentsAsync(KernelProcessStepContext context, List<string> fishActions, List<string> potatoActions)
        {
            Console.WriteLine($"ADD_CONDIMENTS: Added condiments to Fish & Chips - Fish: {JsonSerializer.Serialize(fishActions)}, Potatoes: {JsonSerializer.Serialize(potatoActions)}");
            fishActions.AddRange(potatoActions);
            fishActions.Add(FoodIngredients.Condiments.ToFriendlyString());
            await context.EmitEventAsync(StepEvents.CondimentsAdded, fishActions);
        }
    }

    private sealed class ExternalFishAndChipsStep : ExternalStep
    {
        public static new class StepEvents
        {
            public static readonly KernelProcessEventDescriptor<List<string>> FishAndChipsReady = new(nameof(ProcessEvents.FishAndChipsReady));
        }

        public ExternalFishAndChipsStep() : base(ProcessEvents.FishAndChipsReady) { }
    }
}
