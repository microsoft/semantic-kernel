// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process.IntegrationTests;

#pragma warning disable CS1591 // Missing XML comment for publicly visible type or member

/// <summary>
/// A step that contains a map operation that emits two events.
/// </summary>
public sealed class ComputeStep : KernelProcessStep
{
    public const string SquareEventId = "SquareResult";
    public const string CubicEventId = "CubicResult";
    public const string ComputeFunction = "MapCompute";

    [KernelFunction(ComputeFunction)]
    public async ValueTask ComputeAsync(KernelProcessStepContext context, long value)
    {
        long square = value * value;
        await context.EmitEventAsync(new() { Id = SquareEventId, Data = square });
        await context.EmitEventAsync(new() { Id = CubicEventId, Data = square * value });
    }
}

/// <summary>
/// State for union step to capture results.
/// </summary>
public sealed record UnionState
{
    public long SquareResult { get; set; }
    public long CubicResult { get; set; }
};

/// <summary>
/// The step that combines the results of the map operation.
/// </summary>
public sealed class UnionStep : KernelProcessStep<UnionState>
{
    public const string EventId = "MapUnion";
    public const string SumSquareFunction = "UnionSquare";
    public const string SumCubicFunction = "UnionCubic";

    private UnionState _state = new();

    public override ValueTask ActivateAsync(KernelProcessStepState<UnionState> state)
    {
        this._state = state.State ?? throw new InvalidDataException();

        return ValueTask.CompletedTask;
    }

    [KernelFunction(SumSquareFunction)]
    public void SumSquare(IList<long> values)
    {
        long sum = values.Sum();
        this._state.SquareResult = sum;
    }

    [KernelFunction(SumCubicFunction)]
    public void SumCubic(IList<long> values)
    {
        long sum = values.Sum();
        this._state.CubicResult = sum;
    }
}
