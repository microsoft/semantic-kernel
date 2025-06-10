// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Sample process that showcases how to create a selecting fan out process
/// For a visual reference of the FriedFishProcess check this <see href="https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/README.md#single-order-preparation-process" >diagram</see>
/// </summary>
public static class SingleFoodItemProcess
{
    public static class ProcessEvents
    {
        public const string SingleOrderReceived = nameof(SingleOrderReceived);
        public const string SingleOrderReady = nameof(SingleOrderReady);
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
        var externalStep = processBuilder.AddStepFromType<ExternalSingleOrderStep>();

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

        packOrderStep
            .OnEvent(PackOrderStep.OutputEvents.FoodPacked)
            .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));

        return processBuilder;
    }

    private sealed class DispatchSingleOrderStep : KernelProcessStep
    {
        public static class ProcessFunctions
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

        [KernelFunction(ProcessFunctions.PrepareSingleOrder)]
        public async Task DispatchSingleOrderAsync(KernelProcessStepContext context, FoodItem foodItem)
        {
            var foodName = foodItem.ToFriendlyString();
            Console.WriteLine($"DISPATCH_SINGLE_ORDER: Dispatching '{foodName}'!");
            var foodActions = new List<string>();

            switch (foodItem)
            {
                case FoodItem.PotatoFries:
                    await context.EmitEventAsync(new() { Id = OutputEvents.PrepareFries, Data = foodActions });
                    break;
                case FoodItem.FriedFish:
                    await context.EmitEventAsync(new() { Id = OutputEvents.PrepareFriedFish, Data = foodActions });
                    break;
                case FoodItem.FishSandwich:
                    await context.EmitEventAsync(new() { Id = OutputEvents.PrepareFishSandwich, Data = foodActions });
                    break;
                case FoodItem.FishAndChips:
                    await context.EmitEventAsync(new() { Id = OutputEvents.PrepareFishAndChips, Data = foodActions });
                    break;
                default:
                    break;
            }
        }
    }

    private sealed class PackOrderStep : KernelProcessStep
    {
        public static class ProcessFunctions
        {
            public const string PackFood = nameof(PackFood);
        }
        public static class OutputEvents
        {
            public const string FoodPacked = nameof(FoodPacked);
        }

        [KernelFunction(ProcessFunctions.PackFood)]
        public async Task PackFoodAsync(KernelProcessStepContext context, List<string> foodActions)
        {
            Console.WriteLine($"PACKING_FOOD: Food {foodActions.First()} Packed! - {JsonSerializer.Serialize(foodActions)}");
            await context.EmitEventAsync(new() { Id = OutputEvents.FoodPacked });
        }
    }

    private sealed class ExternalSingleOrderStep : ExternalStep
    {
        public ExternalSingleOrderStep() : base(ProcessEvents.SingleOrderReady) { }
    }
}
