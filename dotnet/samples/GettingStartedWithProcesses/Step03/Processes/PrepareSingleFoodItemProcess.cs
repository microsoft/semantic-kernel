// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Events to be used in the process <see cref="PrepareSingleFoodItemProcess"/>
/// </summary>
public enum PrepareSingleOrderEvents
{
    SingleOrderReceived,
    DispatchSingleOrder,
    DispatchPotatoFries,
    PreparePotatoFries,
    DispatchFriedFish,
    PrepareFriedFish,
    DispatchFishSandwich,
    PrepareFishSandwich,
    DispatchFishAndChips,
    PrepareFishAndChips,
    SingleOrderReady,
    PackFood,
    FoodPacked,
}

/// <summary>
/// Sample process that showcases how to create a selecting fan out process
/// </summary>
public class PrepareSingleFoodItemProcess : ProcessEventStepMapper<PrepareSingleOrderEvents>
{
    public PrepareSingleFoodItemProcess(string processName = nameof(PrepareSingleFoodItemProcess)) : base(processName)
    {
        // Adding existing steps
        this.AddStepFromType<DispatchSingleOrderStep>(new() {
            { PrepareSingleOrderEvents.DispatchSingleOrder, new() {
                StepOutputEvents =          {
                    { PrepareSingleOrderEvents.DispatchFriedFish, DispatchSingleOrderStep.OutputEvents.PrepareFriedFish },
                    { PrepareSingleOrderEvents.DispatchPotatoFries, DispatchSingleOrderStep.OutputEvents.PrepareFries },
                    { PrepareSingleOrderEvents.DispatchFishSandwich, DispatchSingleOrderStep.OutputEvents.PrepareFishSandwich },
                    { PrepareSingleOrderEvents.DispatchFishAndChips, DispatchSingleOrderStep.OutputEvents.PrepareFishAndChips },
            } } } });

        this.AddStepFromType<MockPrepareFriedFishStep>(new() { {
            PrepareSingleOrderEvents.PrepareFriedFish, new () {
                StepOutputEvents = {
                    { PrepareSingleOrderEvents.SingleOrderReady, MockPreparationFoodStep.OutputEvents.FoodReady },
            } } } });

        this.AddStepFromType<MockPreparePotatoFriesStep>(new() { {
            PrepareSingleOrderEvents.PreparePotatoFries, new () {
                StepOutputEvents = {
                    { PrepareSingleOrderEvents.SingleOrderReady, MockPreparationFoodStep.OutputEvents.FoodReady },
            } } } });

        this.AddStepFromType<MockPrepareFishSandwichStep>(new() { {
            PrepareSingleOrderEvents.PrepareFishSandwich, new () {
                StepOutputEvents = {
                    { PrepareSingleOrderEvents.SingleOrderReady, MockPreparationFoodStep.OutputEvents.FoodReady },
            } } } });

        this.AddStepFromType<MockPrepareFishAndChipsStep>(new() { {
            PrepareSingleOrderEvents.PrepareFishAndChips, new () {
                StepOutputEvents = {
                    { PrepareSingleOrderEvents.SingleOrderReady, MockPreparationFoodStep.OutputEvents.FoodReady },
            } } } });

        this.AddStepFromType<PackOrderStep>(new() { {
            PrepareSingleOrderEvents.PackFood, new () {
                StepOutputEvents = {
                    { PrepareSingleOrderEvents.FoodPacked, PackOrderStep.OutputEvents.FoodPacked },
            } } } });

        // Linking internal events
        this.LinkInternalEvents(PrepareSingleOrderEvents.DispatchPotatoFries, PrepareSingleOrderEvents.PreparePotatoFries);
        this.LinkInternalEvents(PrepareSingleOrderEvents.DispatchFriedFish, PrepareSingleOrderEvents.PrepareFriedFish);
        this.LinkInternalEvents(PrepareSingleOrderEvents.DispatchFishSandwich, PrepareSingleOrderEvents.PrepareFishSandwich);
        this.LinkInternalEvents(PrepareSingleOrderEvents.DispatchFishAndChips, PrepareSingleOrderEvents.PrepareFishAndChips);

        // When multiple steps output the same event, it is better to use the event linked to the source step instead of the output event name (ex: 'SingleOrderReady')
        this.LinkInternalEvents(PrepareSingleOrderEvents.PreparePotatoFries, PrepareSingleOrderEvents.PackFood);
        this.LinkInternalEvents(PrepareSingleOrderEvents.PrepareFriedFish, PrepareSingleOrderEvents.PackFood);
        this.LinkInternalEvents(PrepareSingleOrderEvents.PrepareFishSandwich, PrepareSingleOrderEvents.PackFood);
        this.LinkInternalEvents(PrepareSingleOrderEvents.PrepareFishAndChips, PrepareSingleOrderEvents.PackFood);

        // Linking external input events
        this.LinkExternalInputEvent(PrepareSingleOrderEvents.SingleOrderReceived, PrepareSingleOrderEvents.DispatchSingleOrder);

        // Linking external output events
        this.LinkExternalOutputEvent(PrepareSingleOrderEvents.PackFood, PrepareSingleOrderEvents.FoodPacked);
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
