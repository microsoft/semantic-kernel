// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// %%% TBD
/// </summary>
internal sealed class MapStep<TValue> : KernelProcessStep
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
    public async ValueTask MapAsync(KernelProcessStepContext context, TValue[] values, Kernel kernel)
    {
        //// Fan out to parallel processes
        //Task<LocalKernelProcessContext>[] runningProcesses =
        //[
        //    ..values.Select(
        //        value =>
        //            this.CreateProcess().StartAsync(
        //                kernel,
        //                new KernelProcessEvent
        //                {
        //                    Id = this._startEventId,
        //                    Data = value
        //                }))
        //];

        //await Task.WhenAll(runningProcesses).ConfigureAwait(false);

        //// Capture process results
        //TValue[] results = new TValue[runningProcesses.Length];
        //for (int index = 0; index < runningProcesses.Length; ++index)
        //{
        //    var processInfo = await runningProcesses[index].Result.GetStateAsync();
        //    results[index] =
        //        processInfo.Steps
        //            .Where(step => step.State.Name == nameof(CaptureStep))
        //            .Select(step => step.State)
        //            .OfType<KernelProcessStepState<CaptureState>>()
        //            .Single()
        //            .State!
        //            .Value;
        //}

        await context.EmitEventAsync(new() { Id = this._completeEventId, Data = values }).ConfigureAwait(false);
        //await context.EmitEventAsync(new() { Id = this._completeEventId, Data = results }).ConfigureAwait(false);
    }
}
