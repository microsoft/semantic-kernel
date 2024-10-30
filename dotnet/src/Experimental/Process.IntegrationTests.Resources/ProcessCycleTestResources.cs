using System;
using System.Runtime.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Kick off step for the process.
/// </summary>
public sealed class KickoffStep : KernelProcessStep
{
    public static class Functions
    {
        public const string KickOff = nameof(KickOff);
    }

    [KernelFunction(Functions.KickOff)]
    public async ValueTask PrintWelcomeMessageAsync(KernelProcessStepContext context)
    {
        await context.EmitEventAsync(new() { Id = CommonEvents.StartARequested, Data = "Get Going A" });
        await context.EmitEventAsync(new() { Id = CommonEvents.StartBRequested, Data = "Get Going B" });
    }
}

/// <summary>
/// A step in the process.
/// </summary>
public sealed class AStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context)
    {
        await Task.Delay(TimeSpan.FromSeconds(1));
        await context.EmitEventAsync(new() { Id = CommonEvents.AStepDone, Data = "I did A" });
    }
}

/// <summary>
/// A step in the process.
/// </summary>
public sealed class BStep : KernelProcessStep
{
    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context)
    {
        await Task.Delay(TimeSpan.FromSeconds(2));
        await context.EmitEventAsync(new() { Id = CommonEvents.BStepDone, Data = "I did B" });
    }
}

/// <summary>
/// A step in the process.
/// </summary>
public sealed class CStep : KernelProcessStep<CStepState>
{
    private CStepState? _state = new();

    public override ValueTask ActivateAsync(KernelProcessStepState<CStepState> state)
    {
        this._state = state.State;
        return base.ActivateAsync(state);
    }

    [KernelFunction]
    public async ValueTask DoItAsync(KernelProcessStepContext context, string astepdata, string bstepdata)
    {
        this._state!.CurrentCycle++;
        if (this._state.CurrentCycle == 3)
        {
            // Exit the processes
            await context.EmitEventAsync(new() { Id = CommonEvents.ExitRequested });
            return;
        }

        // Cycle back to the start
        await context.EmitEventAsync(new() { Id = CommonEvents.CStepDone });
    }
}

/// <summary>
/// A state object for the CStep.
/// </summary>
[DataContract]
public sealed record CStepState
{
    [DataMember]
    public int CurrentCycle { get; set; }
}

/// <summary>
/// Common Events used in the process.
/// </summary>
public static class CommonEvents
{
    public const string UserInputReceived = nameof(UserInputReceived);
    public const string CompletionResponseGenerated = nameof(CompletionResponseGenerated);
    public const string WelcomeDone = nameof(WelcomeDone);
    public const string AStepDone = nameof(AStepDone);
    public const string BStepDone = nameof(BStepDone);
    public const string CStepDone = nameof(CStepDone);
    public const string StartARequested = nameof(StartARequested);
    public const string StartBRequested = nameof(StartBRequested);
    public const string ExitRequested = nameof(ExitRequested);
    public const string StartProcess = nameof(StartProcess);
}

