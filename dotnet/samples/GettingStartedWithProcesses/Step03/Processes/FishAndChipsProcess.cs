﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with a fan in/fan out behavior and use of existing processes as steps.<br/>
/// Visual reference of this process can be found in the <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#Fish_And_Chips_Preparation_Process" >diagram</see>
/// </summary>
public static class FishAndChipsProcess
{
    public static class ProcessEvents
    {
        public const string PrepareFishAndChips = nameof(PrepareFishAndChips);
        public const string FishAndChipsReady = nameof(FishAndChipsReady);
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
            .SendEventTo(makeFriedFishStep.WhereInputEventIs(FriedFishProcess.ProcessEvents.PrepareFriedFish));

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFishAndChips)
            .SendEventTo(makePotatoFriesStep.WhereInputEventIs(PotatoFriesProcess.ProcessEvents.PreparePotatoFries));

        makeFriedFishStep
            .OnEvent(FriedFishProcess.ProcessEvents.FriedFishReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(addCondimentsStep, parameterName: "fishActions"));

        makePotatoFriesStep
            .OnEvent(PotatoFriesProcess.ProcessEvents.PotatoFriesReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(addCondimentsStep, parameterName: "potatoActions"));

        addCondimentsStep
            .OnEvent(AddFishAndChipsCondimentsStep.OutputEvents.CondimentsAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));

        return processBuilder;
    }

    private sealed class AddFishAndChipsCondimentsStep : KernelProcessStep
    {
        public static class Functions
        {
            public const string AddCondiments = nameof(AddCondiments);
        }

        public static class OutputEvents
        {
            public const string CondimentsAdded = nameof(CondimentsAdded);
        }

        [KernelFunction(Functions.AddCondiments)]
        public async Task AddCondimentsAsync(KernelProcessStepContext context, List<string> fishActions, List<string> potatoActions)
        {
            Console.WriteLine($"ADD_CONDIMENTS: Added condiments to Fish & Chips - Fish: {JsonSerializer.Serialize(fishActions)}, Potatoes: {JsonSerializer.Serialize(potatoActions)}");
            fishActions.AddRange(potatoActions);
            fishActions.Add(FoodIngredients.Condiments.ToFriendlyString());
            await context.EmitEventAsync(new() { Id = OutputEvents.CondimentsAdded, Data = fishActions });
        }
    }

    private sealed class ExternalFishAndChipsStep : ExternalStep
    {
        public ExternalFishAndChipsStep() : base(ProcessEvents.FishAndChipsReady) { }
    }
}
