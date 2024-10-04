// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Step03.Models;
using Step03.Steps;

namespace Step03.Processes;

/// <summary>
/// Events to be used in the process <see cref="PrepareFishSandwichProcess"/>
/// </summary>
public enum PrepareFishAndChipsEvents
{
    /// <summary>
    /// External input trigger event
    /// </summary>
    PrepareFishAndChips,
    /// <summary>
    /// Event that triggers the preparation of fried fish
    /// </summary>
    PrepareFriedFish,
    /// <summary>
    /// Output event from the step PrepareFriedFish
    /// </summary>
    FriedFishReady,
    /// <summary>
    /// Event that triggers the preparation of fried potatoes
    /// </summary>
    PreparePotatoFries,
    /// <summary>
    /// Output event from the step PreparePotatoFries
    /// </summary>
    PotatoFriesReady,
    /// <summary>
    /// Event that pipes the readiness of the fish to the add condiment step
    /// </summary>
    AddCondimentsToFish,
    /// <summary>
    /// Event that pipes the readiness of the potatoes to the add condiment step
    /// </summary>
    AddCondimentsToPotato,
    /// <summary>
    /// Output event from the AddCondiment step
    /// </summary>
    CondimentsAdded,
    /// <summary>
    /// Event to be linked to the last step of the process -> External Output Event
    /// </summary>
    FishAndChipsReady,
}

/// <summary>
/// Sample process that showcases how to create a process with a fan in/fan out behavior
/// Visual reference of this process can be found in the <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#Fish_And_Chips_Preparation_Process" >diagram</see>
/// </summary>
public class PrepareFishAndChipsProcess : ProcessEventStepMapper<PrepareFishAndChipsEvents>
{
    public PrepareFishAndChipsProcess(string processName = nameof(PrepareFishAndChipsProcess)) : base(processName)
    {
        // Adding existing steps
        this.AddStepFromType<MockPrepareFriedFishStep>(new() {
            { PrepareFishAndChipsEvents.PrepareFriedFish, new() {
                StepOutputEvents =          {
                    { PrepareFishAndChipsEvents.FriedFishReady, MockPrepareFriedFishStep.OutputEvents.FoodReady },
            } } } });

        this.AddStepFromType<MockPreparePotatoFriesStep>(new() {
            { PrepareFishAndChipsEvents.PreparePotatoFries, new() {
                StepOutputEvents =          {
                    { PrepareFishAndChipsEvents.PotatoFriesReady, MockPreparePotatoFriesStep.OutputEvents.FoodReady },
            } } } });

        // When a step has multiple parameters, the should be an individual event per parameter and output the same event type
        this.AddStepFromType<AddFishAndChipsCondimentsStep>(new() {
            { PrepareFishAndChipsEvents.AddCondimentsToFish, new() {
                ParameterName = "fishPrepared", StepOutputEvents = { { PrepareFishAndChipsEvents.CondimentsAdded, AddFishAndChipsCondimentsStep.OutputEvents.CondimentsAdded } } } },
            { PrepareFishAndChipsEvents.AddCondimentsToPotato, new() {
                ParameterName = "potatoFriesPrepared", StepOutputEvents = { { PrepareFishAndChipsEvents.CondimentsAdded, AddFishAndChipsCondimentsStep.OutputEvents.CondimentsAdded } } } } });

        // Linking internal events - if there is only 1 output event per step, the event linked to the step or the output step event can be referenced
        this.LinkInternalEvents(PrepareFishAndChipsEvents.FriedFishReady, PrepareFishAndChipsEvents.AddCondimentsToFish);
        this.LinkInternalEvents(PrepareFishAndChipsEvents.PotatoFriesReady, PrepareFishAndChipsEvents.AddCondimentsToPotato);

        // Linking external input events
        this.LinkExternalInputEvent(PrepareFishAndChipsEvents.PrepareFishAndChips, PrepareFishAndChipsEvents.PrepareFriedFish);
        this.LinkExternalInputEvent(PrepareFishAndChipsEvents.PrepareFishAndChips, PrepareFishAndChipsEvents.PreparePotatoFries);

        // Linking external output events
        this.LinkExternalOutputEvent(PrepareFishAndChipsEvents.CondimentsAdded, PrepareFishAndChipsEvents.FishAndChipsReady);
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
        public async Task AddCondimentsAsync(KernelProcessStepContext context, FoodIngredients fishPrepared, FoodIngredients potatoFriesPrepared)
        {
            Console.WriteLine("ADD_CONDIMENTS: Added condiments to Fish & Chips");
            await context.EmitEventAsync(new() { Id = OutputEvents.CondimentsAdded });
        }
    }
}
