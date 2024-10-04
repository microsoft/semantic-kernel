// Copyright (c) Microsoft. All rights reserved.
/// <summary>
/// The following file describes stage by stage on how to create an SK Process using <see cref="ProcessEventStepMapper{TEvent}"/>
/// </summary>
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Step03.Models;
using Step03.Steps;
namespace Step03.Processes;

/// <summary>
/// Events to be used in the process <see cref="PrepareFriedFishProcess"/>
/// Enum that contains trigger and output events of the process
/// trigger events get linked to specific step functions if needed.<br/>
/// <br/>
/// STAGE 1: Create Process events.
/// <br/><br/>
/// Recommendations:<br/>
/// - Create one event per Step Function used <br/>
/// - If a Step Function outputs multiple events, there should be an event to be mapped with each step internal event <br/>
/// - Create an event for every external input event that can trigger the SK Process <br/>
/// - Create an event for every external output event the process has that could be subscribed to by another process or step if needed <br/>
/// </summary>
public enum FriedFishEvents
{
    /// <summary>
    /// External input trigger event
    /// </summary>
    PrepareFriedFish,
    /// <summary>
    /// Event to be linked to GatherIngredients Step
    /// </summary>
    GatherIngredients,
    /// <summary>
    /// Event to be linked to the GatherIngredients Output Event
    /// </summary>
    IngredientsGathered,
    /// <summary>
    /// Event to be linked to Cut Step -> Chop Function
    /// </summary>
    ChopFish,
    /// <summary>
    /// Event to be linked to the Cut Step Chop Function Output Event
    /// </summary>
    ChoppedFishReady,
    /// <summary>
    /// Event to be linked to Fry Step
    /// </summary>
    FryFish,
    /// <summary>
    /// Event to be linked to the Fry Step Output Event - FriedFoodReady -> External Output Event
    /// </summary>
    FriedFishReady,
    /// <summary>
    /// Event to be linked to the Fry Step Output Event - FoodRuined
    /// </summary>
    FriedFishRuined,
}

/// <summary>
/// STAGE 2: Class that uses as base <see cref="ProcessEventStepMapper{TEvent}"/> to:<br/>
/// 1. Add steps and other subprocess as steps of the SK Process.<br/>
/// 2. Linking of internal process events: Link prorcess steps and subprocess own events with the created SK Process.<br/>
/// 3. Define External Input Event triggers of the SK Process.<br/>
/// 4. Define External Ouput Events of the SK Process that could be subscribed to by other SK Steps or Processes.<br/>
///
/// For a visual reference of the FriedFishProcess check this <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#Fried_Fish_Preparation_Process" >diagram</see>
/// </summary>
public class PrepareFriedFishProcess : ProcessEventStepMapper<FriedFishEvents>
{
    public PrepareFriedFishProcess(string processName = nameof(PrepareFriedFishProcess)) : base(processName)
    {
        // STAGE 2.1:
        // Adding existing SK Steps and linking Step output events to Process events
        // If the SK Step has multiple SK functions, the functionName used by the step should be specified
        // This is the only stage where the Step/Subprocesses events names are referred, for the next stages only the Process Events are used
        this.AddStepFromType<GatherFriedFishIngredientsStep>(new() {
            { FriedFishEvents.GatherIngredients, new() {
                StepOutputEvents = {
                    { FriedFishEvents.IngredientsGathered, GatherFriedFishIngredientsStep.OutputEvents.IngredientsGathered }
            } } } });

        this.AddStepFromType<CutFoodStep>(new() { { FriedFishEvents.ChopFish, new() {
            FunctionName = CutFoodStep.Functions.ChopFood,
            StepOutputEvents = { { FriedFishEvents.ChoppedFishReady, CutFoodStep.OutputEvents.ChoppingReady } } } } });
        // If the SK Step Function emits multiple events, the StepOutputEvents should be specified to map the
        // Step Event Name with a Process Event
        this.AddStepFromType<FryFoodStep>(new() {
            { FriedFishEvents.FryFish, new() {
                StepOutputEvents = {
                    { FriedFishEvents.FriedFishRuined, FryFoodStep.OutputEvents.FoodRuined },
                    { FriedFishEvents.FriedFishReady, FryFoodStep.OutputEvents.FriedFoodReady }}}}});

        // STAGE 2.2:
        // Linking of internal process events - sourceInputEvents should already by linked to a step or subprocess in Stage 2.1
        this.LinkInternalEvents(FriedFishEvents.IngredientsGathered, FriedFishEvents.ChopFish);
        this.LinkInternalEvents(FriedFishEvents.ChoppedFishReady, FriedFishEvents.FryFish);
        this.LinkInternalEvents(FriedFishEvents.FriedFishRuined, FriedFishEvents.GatherIngredients);

        // STAGE 2.3: Linking specific process events
        // Defining which unassigned events are used external events and how they connect with
        // previously defined internal process events
        this.LinkExternalInputEvent(externalSourceEvent: FriedFishEvents.PrepareFriedFish, targetSourceEvent: FriedFishEvents.GatherIngredients);

        // STAGE 2.4
        // 2.3 Defining which internal source output events can be accesses externally outside of this process
        this.LinkExternalOutputEvent(sourceInputEvent: FriedFishEvents.FryFish, sourceOutputExternalEvent: FriedFishEvents.FriedFishReady);
    }

    private sealed class GatherFriedFishIngredientsStep : GatherIngredientsStep
    {
        public override async Task GatherIngredientsAsync(KernelProcessStepContext context)
        {
            var ingredient = FoodIngredients.Fish;
            Console.WriteLine($"GATHER_INGREDIENT: Gathered ingredient {ingredient.ToFriendlyString()}");
            await context.EmitEventAsync(new() { Id = OutputEvents.IngredientsGathered, Data = ingredient });
        }
    }
}
