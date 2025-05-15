// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with sequential steps and use of existing processes as steps.<br/>
/// Visual reference of this process can be found in the <see href="https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/README.md#fish-sandwich-preparation-process" >diagram</see>
/// </summary>
public static class FishSandwichProcess
{
    public static class ProcessEvents
    {
        public const string PrepareFishSandwich = nameof(PrepareFishSandwich);
        public const string FishSandwichReady = nameof(FishSandwichReady);
    }

    public static ProcessBuilder CreateProcess(string processName = "FishSandwichProcess")
    {
        var processBuilder = new ProcessBuilder(processName);
        var makeFriedFishStep = processBuilder.AddStepFromProcess(FriedFishProcess.CreateProcess());
        var addBunsStep = processBuilder.AddStepFromType<AddBunsStep>();
        var addSpecialSauceStep = processBuilder.AddStepFromType<AddSpecialSauceStep>();
        // An additional step that is the only one that emits an public event in a process can be added to maintain event names unique
        var externalStep = processBuilder.AddStepFromType<ExternalFriedFishStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFishSandwich)
            .SendEventTo(makeFriedFishStep.WhereInputEventIs(FriedFishProcess.ProcessEvents.PrepareFriedFish));

        makeFriedFishStep
            .OnEvent(FriedFishProcess.ProcessEvents.FriedFishReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(addBunsStep));

        addBunsStep
            .OnEvent(AddBunsStep.OutputEvents.BunsAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(addSpecialSauceStep));

        addSpecialSauceStep
            .OnEvent(AddSpecialSauceStep.OutputEvents.SpecialSauceAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));

        return processBuilder;
    }

    public static ProcessBuilder CreateProcessWithStatefulStepsV1(string processName = "FishSandwichWithStatefulStepsProcess")
    {
        var processBuilder = new ProcessBuilder(processName) { Version = "FishSandwich.V1" };
        var makeFriedFishStep = processBuilder.AddStepFromProcess(FriedFishProcess.CreateProcessWithStatefulStepsV1());
        var addBunsStep = processBuilder.AddStepFromType<AddBunsStep>();
        var addSpecialSauceStep = processBuilder.AddStepFromType<AddSpecialSauceStep>();
        // An additional step that is the only one that emits an public event in a process can be added to maintain event names unique
        var externalStep = processBuilder.AddStepFromType<ExternalFriedFishStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFishSandwich)
            .SendEventTo(makeFriedFishStep.WhereInputEventIs(FriedFishProcess.ProcessEvents.PrepareFriedFish));

        makeFriedFishStep
            .OnEvent(FriedFishProcess.ProcessEvents.FriedFishReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(addBunsStep));

        addBunsStep
            .OnEvent(AddBunsStep.OutputEvents.BunsAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(addSpecialSauceStep));

        addSpecialSauceStep
            .OnEvent(AddSpecialSauceStep.OutputEvents.SpecialSauceAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));

        return processBuilder;
    }

    public static ProcessBuilder CreateProcessWithStatefulStepsV2(string processName = "FishSandwichWithStatefulStepsProcess")
    {
        var processBuilder = new ProcessBuilder(processName) { Version = "FishSandwich.V2" };
        var makeFriedFishStep = processBuilder.AddStepFromProcess(FriedFishProcess.CreateProcessWithStatefulStepsV2("FriedFishStep"), aliases: ["FriedFishWithStatefulStepsProcess"]);
        var addBunsStep = processBuilder.AddStepFromType<AddBunsStep>();
        var addSpecialSauceStep = processBuilder.AddStepFromType<AddSpecialSauceStep>();
        // An additional step that is the only one that emits an public event in a process can be added to maintain event names unique
        var externalStep = processBuilder.AddStepFromType<ExternalFriedFishStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFishSandwich)
            .SendEventTo(makeFriedFishStep.WhereInputEventIs(FriedFishProcess.ProcessEvents.PrepareFriedFish));

        makeFriedFishStep
            .OnEvent(FriedFishProcess.ProcessEvents.FriedFishReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(addBunsStep));

        addBunsStep
            .OnEvent(AddBunsStep.OutputEvents.BunsAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(addSpecialSauceStep));

        addSpecialSauceStep
            .OnEvent(AddSpecialSauceStep.OutputEvents.SpecialSauceAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));

        return processBuilder;
    }

    private sealed class AddBunsStep : KernelProcessStep
    {
        public static class ProcessFunctions
        {
            public const string AddBuns = nameof(AddBuns);
        }

        public static class OutputEvents
        {
            public const string BunsAdded = nameof(BunsAdded);
        }

        [KernelFunction(ProcessFunctions.AddBuns)]
        public async Task SliceFoodAsync(KernelProcessStepContext context, List<string> foodActions)
        {
            Console.WriteLine($"BUNS_ADDED_STEP: Buns added to ingredient {foodActions.First()}");
            foodActions.Add(FoodIngredients.Buns.ToFriendlyString());
            await context.EmitEventAsync(new() { Id = OutputEvents.BunsAdded, Data = foodActions });
        }
    }

    private sealed class AddSpecialSauceStep : KernelProcessStep
    {
        public static class ProcessFunctions
        {
            public const string AddSpecialSauce = nameof(AddSpecialSauce);
        }

        public static class OutputEvents
        {
            public const string SpecialSauceAdded = nameof(SpecialSauceAdded);
        }

        [KernelFunction(ProcessFunctions.AddSpecialSauce)]
        public async Task SliceFoodAsync(KernelProcessStepContext context, List<string> foodActions)
        {
            Console.WriteLine($"SPECIAL_SAUCE_ADDED: Special sauce added to ingredient {foodActions.First()}");
            foodActions.Add(FoodIngredients.Sauce.ToFriendlyString());
            await context.EmitEventAsync(new() { Id = OutputEvents.SpecialSauceAdded, Data = foodActions, Visibility = KernelProcessEventVisibility.Public });
        }
    }

    private sealed class ExternalFriedFishStep : ExternalStep
    {
        public ExternalFriedFishStep() : base(ProcessEvents.FishSandwichReady) { }
    }
}
