// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Events to be used in the process <see cref="PrepareFishSandwichProcess"/>
/// </summary>
public enum PrepareFishSandwichEvents
{
    /// <summary>
    /// External input trigger event
    /// </summary>
    PrepareFishSandwich,
    /// <summary>
    /// Event that triggers the preparation of fried fish
    /// </summary>
    PrepareFriedFish,
    /// <summary>
    /// Output event from the step PrepareFriedFish
    /// </summary>
    FriedFishReady,
    /// <summary>
    /// Event linked to the Add Buns Step
    /// </summary>
    AddBuns,
    /// <summary>
    /// Output event of the Add Buns Step
    /// </summary>
    BunsAdded,
    /// <summary>
    /// Event linked to the Add Special Sauce Step
    /// </summary>
    AddSpecialSauce,
    /// <summary>
    /// Output event of the Add Special Sauce Step
    /// </summary>
    SpecialSauceAdded,
    /// <summary>
    /// Event to be linked to the last step of the process -> External Output Event
    /// </summary>
    FishSandwichReady,
}

/// <summary>
/// Sample process that showcases how to create a process with sequential steps
/// Visual reference of this process can be found in the <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#Fish_Sandwich_Preparation_Process" >diagram</see>
/// </summary>
public class PrepareFishSandwichProcess : ProcessEventStepMapper<PrepareFishSandwichEvents>
{
    public PrepareFishSandwichProcess(string processName = nameof(PrepareFishSandwichProcess)) : base(processName)
    {
        // Adding existing steps
        this.AddStepFromType<MockPrepareFriedFishStep>(new() {
            { PrepareFishSandwichEvents.PrepareFriedFish, new() {
                StepOutputEvents =          {
                    { PrepareFishSandwichEvents.FriedFishReady, MockPrepareFriedFishStep.OutputEvents.FoodReady },
            } } } });

        this.AddStepFromType<AddBunsStep>(new() {
            { PrepareFishSandwichEvents.AddBuns, new() {
                StepOutputEvents =          {
                    { PrepareFishSandwichEvents.BunsAdded, AddBunsStep.OutputEvents.BunsAdded },
            } } } });

        this.AddStepFromType<AddSpecialSauceStep>(new() {
            { PrepareFishSandwichEvents.AddSpecialSauce, new() {
                StepOutputEvents =          {
                    { PrepareFishSandwichEvents.SpecialSauceAdded, AddSpecialSauceStep.OutputEvents.SpecialSauceAdded },
            } } } });

        // Linking internal events - if there is only 1 output event per step, the event linked to the step or the output step event can be referenced
        this.LinkInternalEvents(PrepareFishSandwichEvents.FriedFishReady, PrepareFishSandwichEvents.AddBuns);
        this.LinkInternalEvents(PrepareFishSandwichEvents.BunsAdded, PrepareFishSandwichEvents.AddSpecialSauce);

        // Linking external input events
        this.LinkExternalInputEvent(PrepareFishSandwichEvents.PrepareFishSandwich, PrepareFishSandwichEvents.PrepareFriedFish);

        // Linking external output events
        this.LinkExternalOutputEvent(PrepareFishSandwichEvents.SpecialSauceAdded, PrepareFishSandwichEvents.FishSandwichReady);
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
            await context.EmitEventAsync(new() { Id = OutputEvents.SpecialSauceAdded });
        }
    }
}
