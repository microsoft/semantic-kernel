// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step04;

/// <summary>
/// %%% TBD
/// </summary>
public sealed class MapStep<TValue> : KernelProcessStep
{
    private readonly ProcessStepBuilder _builder;
    private readonly string _startEventId;
    private readonly string _completeEventId;

    public MapStep(ProcessStepBuilder builder, string startEventId, string completeEventId)
    {
        this._builder = builder;
        this._startEventId = startEventId;
        this._completeEventId = completeEventId;
    }

    [KernelFunction]
    public async ValueTask MapAsync(KernelProcessStepContext context, TValue[] values, Kernel kernel) // %%% IEnumerable ???
    {
        // Fan out to parallel processes
        Task<LocalKernelProcessContext>[] runningProcesses =
        [
            ..values.Select(
                value =>
                    CreateProcess().StartAsync(
                        kernel,
                        new KernelProcessEvent
                        {
                            Id = this._startEventId,
                            Data = value
                        }))
        ];

        await Task.WhenAll(runningProcesses);

        // Capture process results
        TValue[] results = new TValue[runningProcesses.Length];
        for (int index = 0; index < runningProcesses.Length; ++index)
        {
            var processInfo = await runningProcesses[index].Result.GetStateAsync();
            results[index] =
                processInfo.Steps
                    .Where(step => step.State.Name == nameof(CaptureStep))
                    .Select(step => step.State)
                    .OfType<KernelProcessStepState<CaptureState>>()
                    .Single()
                    .State!
                    .Value;
        }

        await context.EmitEventAsync(new() { Id = this._completeEventId, Data = results });
    }

    private KernelProcess CreateProcess()
    {
        ProcessBuilder mapBuilder = new(nameof(MapStep<TValue>));

        var captureStep = mapBuilder.AddStepFromType<CaptureStep>();

        ProcessStepBuilder externalStep;
        if (_builder is ProcessBuilder builder)
        {
            // If external step is process, initialize appropriately
            var externalProcess = mapBuilder.AddStepFromProcess(builder);
            mapBuilder
                .OnInputEvent(this._startEventId)
                .SendEventTo(externalProcess);
            externalStep = externalProcess;
        }
        else
        {
            // Otherwise treat as step
            externalStep = this._builder;
            mapBuilder
                .OnInputEvent(this._startEventId)
                .SendEventTo(new ProcessFunctionTargetBuilder(externalStep));
        }

        externalStep
            .OnEvent(this._completeEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(captureStep));

        return mapBuilder.Build();
    }

    private sealed record CaptureState
    {
        public TValue Value { get; set; }
    };

    private sealed class CaptureStep : KernelProcessStep<CaptureState>
    {
        private CaptureState? _capture;

        public override ValueTask ActivateAsync(KernelProcessStepState<CaptureState> state)
        {
            this._capture = state.State;
            return default;
        }

        [KernelFunction]
        public void Compute(TValue value)
        {
            this._capture!.Value = value;
        }
    }
}
