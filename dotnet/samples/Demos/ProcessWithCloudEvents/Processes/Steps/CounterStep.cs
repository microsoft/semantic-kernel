// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithCloudEvents.Processes.Steps;

public class CounterStep : KernelProcessStep<CounterStepState>
{
    public static class StepFunctions
    {
        public const string IncreaseCounter = nameof(IncreaseCounter);
        public const string DecreaseCounter = nameof(DecreaseCounter);
        public const string ResetCounter = nameof(ResetCounter);
    }

    public static class OutputEvents
    {
        public const string CounterResult = nameof(CounterResult);
    }

    internal CounterStepState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<CounterStepState> state)
    {
        this._state = state.State;
        return ValueTask.CompletedTask;
    }

    [KernelFunction(StepFunctions.IncreaseCounter)]
    public async Task<int> IncreaseCounterAsync(KernelProcessStepContext context)
    {
        this._state!.Counter += this._state.CounterIncrements;

        if (this._state!.Counter > 5)
        {
            await context.EmitEventAsync(OutputEvents.CounterResult, this._state.Counter);
        }
        this._state.LastCounterUpdate = DateTime.UtcNow;

        return this._state.Counter;
    }

    [KernelFunction(StepFunctions.DecreaseCounter)]
    public async Task<int> DecreaseCounterAsync(KernelProcessStepContext context)
    {
        this._state!.Counter -= this._state.CounterIncrements;

        if (this._state!.Counter > 5)
        {
            await context.EmitEventAsync(OutputEvents.CounterResult, this._state.Counter);
        }
        this._state.LastCounterUpdate = DateTime.UtcNow;

        return this._state.Counter;
    }

    [KernelFunction(StepFunctions.ResetCounter)]
    public async Task<int> ResetCounterAsync(KernelProcessStepContext context)
    {
        this._state!.Counter = 0;
        return this._state.Counter;
    }
}

public class CounterStepState
{
    public int Counter { get; set; } = 0;
    public int CounterIncrements { get; set; } = 1;

    public DateTime? LastCounterUpdate { get; set; } = null;
}
