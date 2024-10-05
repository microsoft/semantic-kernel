// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;

namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a process with sequential steps and use of existing processes as steps.<br/>
/// Visual reference of this process can be found in the <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#Fish_Sandwich_Preparation_Process" >diagram</see>
/// </summary>
public static class FishSandwichProcess
{
    public static class ProcessEvents
    {
        public const string PrepareFishSandwich = nameof(PrepareFishSandwich);
        public const string FishSandwichReady = AddBunsStep.OutputEvents.BunsAdded;
    }

    public static ProcessBuilder CreateProcess(string processName = "FishSandwichProcess")
    {
        var processBuilder = new ProcessBuilder(processName);
        var makeFriedFishStep = processBuilder.AddStepFromProcess(FriedFishProcess.CreateProcess());
        var addBunsStep = processBuilder.AddStepFromType<AddBunsStep>();
        var addSpecialSauceStep = processBuilder.AddStepFromType<AddSpecialSauceStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.PrepareFishSandwich)
            .SendEventTo(makeFriedFishStep.WhereInputEventIs(FriedFishProcess.ProcessEvents.PrepareFriedFish));

        makeFriedFishStep
            .OnEvent(FriedFishProcess.ProcessEvents.FriedFishReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(addBunsStep));

        addBunsStep
            .OnEvent(AddBunsStep.OutputEvents.BunsAdded)
            .SendEventTo(new ProcessFunctionTargetBuilder(addSpecialSauceStep));

        return processBuilder;
    }

    private sealed class AddBunsStep : KernelProcessStep
    {
        public static class Functions
        {
            public const string AddBuns = nameof(AddBuns);
        }

        public static class OutputEvents
        {
            public const string BunsAdded = nameof(BunsAdded);
        }

        [KernelFunction(Functions.AddBuns)]
        public async Task SliceFoodAsync(KernelProcessStepContext context, FoodIngredients food)
        {
            Console.WriteLine($"BUNS_ADDED_STEP: Buns added to ingredient {food.ToFriendlyString()}");
            await context.EmitEventAsync(new() { Id = OutputEvents.BunsAdded, Data = food });
        }
    }

    private sealed class AddSpecialSauceStep : KernelProcessStep
    {
        public static class Functions
        {
            public const string AddSpecialSauce = nameof(AddSpecialSauce);
        }

        public static class OutputEvents
        {
            public const string SpecialSauceAdded = nameof(SpecialSauceAdded);
        }

        [KernelFunction(Functions.AddSpecialSauce)]
        public async Task SliceFoodAsync(KernelProcessStepContext context, FoodIngredients food)
        {
            Console.WriteLine($"SPECIAL_SAUCE_ADDED: Special sauce added to ingredient {food.ToFriendlyString()}");
            await context.EmitEventAsync(new() { Id = OutputEvents.SpecialSauceAdded, Visibility = KernelProcessEventVisibility.Public });
        }
    }
}
