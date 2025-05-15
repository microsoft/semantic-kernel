// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using Microsoft.SemanticKernel;

namespace ProcessWithDapr.ProcessSteps;

/// <summary>
/// A stateful step in the process. This step uses <see cref="CStepState"/> as the persisted
/// state object and overrides the ActivateAsync method to initialize the state when activated.
/// </summary>
internal sealed class CStep : KernelProcessStep<CStepState>
{
    private CStepState? _state;

    // ################ Using persisted state #################
    // CStep has state that we want to be persisted in the process. To ensure that the step always
    // starts with the previously persisted or configured state, we need to override the ActivateAsync
    // method and use the state object it provides.
    public override ValueTask ActivateAsync(KernelProcessStepState<CStepState> state)
    {
        this._state = state.State!;
        Console.WriteLine($"##### CStep activated with Cycle = '{state.State?.CurrentCycle}'.");
        return base.ActivateAsync(state);
    }

    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context, string astepdata, string bstepdata)
    {
        // ########### This method will restart the process in a loop until CurrentCycle >= 3 ###########
        this._state!.CurrentCycle++;
        if (this._state.CurrentCycle >= 3)
        {
            // Exit the processes
            Console.WriteLine("##### CStep run cycle 3 - exiting.");
            await context.EmitEventAsync(new() { Id = CommonEvents.ExitRequested });
            return;
        }

        // Cycle back to the start
        Console.WriteLine($"##### CStep run cycle {this._state.CurrentCycle}.");
        await context.EmitEventAsync(new() { Id = CommonEvents.CStepDone });
    }
}

/// <summary>
/// A state object for the CStep.
/// </summary>
[DataContract]
internal sealed record CStepState
{
    [DataMember]
    public int CurrentCycle { get; set; }
}
