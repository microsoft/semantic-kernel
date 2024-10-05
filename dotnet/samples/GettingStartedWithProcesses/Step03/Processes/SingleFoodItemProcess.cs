﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;

namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a selecting fan out process
/// For a visual reference of the FriedFishProcess check this <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#Single_Order_Preparation_Process" >diagram</see>
/// </summary>
public static class SingleFoodItemProcess
{
    public static class ProcessEvents
    {
        public const string SingleOrderReceived = nameof(SingleOrderReceived);
        public const string SingleOrderReady = PackOrderStep.OutputEvents.FoodPacked;
    }

    public static ProcessBuilder CreateProcess(string processName = "SingleFoodItemProcess")
    {
        var processBuilder = new ProcessBuilder(processName);

        var dispatchOrderStep = processBuilder.AddStepFromType<DispatchSingleOrderStep>();
        var makeFriedFishStep = processBuilder.AddStepFromProcess(FriedFishProcess.CreateProcess());
        var makePotatoFriesStep = processBuilder.AddStepFromProcess(PotatoFriesProcess.CreateProcess());
        var makeFishSandwichStep = processBuilder.AddStepFromProcess(FishSandwichProcess.CreateProcess());
        var makeFishAndChipsStep = processBuilder.AddStepFromProcess(FishAndChipsProcess.CreateProcess());
        var packOrderStep = processBuilder.AddStepFromType<PackOrderStep>();

        processBuilder
            .OnInputEvent(ProcessEvents.SingleOrderReceived)
            .SendEventTo(new ProcessFunctionTargetBuilder(dispatchOrderStep));

        dispatchOrderStep
            .OnEvent(DispatchSingleOrderStep.OutputEvents.PrepareFriedFish)
            .SendEventTo(makeFriedFishStep.WhereInputEventIs(FriedFishProcess.ProcessEvents.PrepareFriedFish));

        dispatchOrderStep
            .OnEvent(DispatchSingleOrderStep.OutputEvents.PrepareFries)
            .SendEventTo(makePotatoFriesStep.WhereInputEventIs(PotatoFriesProcess.ProcessEvents.PreparePotatoFries));

        dispatchOrderStep
            .OnEvent(DispatchSingleOrderStep.OutputEvents.PrepareFishSandwich)
            .SendEventTo(makeFishSandwichStep.WhereInputEventIs(FishSandwichProcess.ProcessEvents.PrepareFishSandwich));

        dispatchOrderStep
            .OnEvent(DispatchSingleOrderStep.OutputEvents.PrepareFishAndChips)
            .SendEventTo(makeFishAndChipsStep.WhereInputEventIs(FishAndChipsProcess.ProcessEvents.PrepareFishAndChips));

        makeFriedFishStep
            .OnEvent(FriedFishProcess.ProcessEvents.FriedFishReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(packOrderStep));

        makePotatoFriesStep
            .OnEvent(PotatoFriesProcess.ProcessEvents.PotatoFriesReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(packOrderStep));

        makeFishSandwichStep
            .OnEvent(FishSandwichProcess.ProcessEvents.FishSandwichReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(packOrderStep));

        makeFishAndChipsStep
            .OnEvent(FishAndChipsProcess.ProcessEvents.FishAndChipsReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(packOrderStep));

        return processBuilder;
    }

    private sealed class DispatchSingleOrderStep : KernelProcessStep
    {
        public static class Functions
        {
            public const string PrepareSingleOrder = nameof(PrepareSingleOrder);
        }

        public static class OutputEvents
        {
            public const string PrepareFries = nameof(PrepareFries);
            public const string PrepareFriedFish = nameof(PrepareFriedFish);
            public const string PrepareFishSandwich = nameof(PrepareFishSandwich);
            public const string PrepareFishAndChips = nameof(PrepareFishAndChips);
        }

        [KernelFunction(Functions.PrepareSingleOrder)]
        public async Task DispatchSingleOrderAsync(KernelProcessStepContext context, FoodItem foodItem)
        {
            var foodName = foodItem.ToFriendlyString();
            Console.WriteLine($"DISPATCH_SINGLE_ORDER: Dispatching '{foodName}'!");

            switch (foodItem)
            {
                case FoodItem.PotatoFries:
                    await context.EmitEventAsync(new() { Id = OutputEvents.PrepareFries, Data = foodName });
                    break;
                case FoodItem.FriedFish:
                    await context.EmitEventAsync(new() { Id = OutputEvents.PrepareFriedFish, Data = foodName });
                    break;
                case FoodItem.FishSandwich:
                    await context.EmitEventAsync(new() { Id = OutputEvents.PrepareFishSandwich, Data = foodName });
                    break;
                case FoodItem.FishAndChips:
                    await context.EmitEventAsync(new() { Id = OutputEvents.PrepareFishAndChips, Data = foodName });
                    break;
                default:
                    break;
            }
        }
    }

    private sealed class PackOrderStep : KernelProcessStep
    {
        public static class Functions
        {
            public const string PackFood = nameof(PackFood);
        }
        public static class OutputEvents
        {
            public const string FoodPacked = nameof(FoodPacked);
        }

        [KernelFunction(Functions.PackFood)]
        public async Task PackFoodAsync(KernelProcessStepContext context, string foodName)
        {
            Console.WriteLine($"PACKING_FOOD: Food {foodName} Packed!");
            await context.EmitEventAsync(new() { Id = OutputEvents.FoodPacked });
        }
    }
}
