// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// %%% COMMENT
/// </summary>
internal sealed record MapResultState<TValue>
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public TValue? Value { get; set; }
};

/// <summary>
/// %%% COMMENT
/// </summary>
internal sealed class MapResultStep<TValue> : KernelProcessStep<MapResultState<TValue>>
{
    private MapResultState<TValue>? _capture;

    /// <inheritdoc/>
    public override ValueTask ActivateAsync(KernelProcessStepState<MapResultState<TValue>> state)
    {
        this._capture = state.State;
        return default;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="value"></param>
    [KernelFunction]
    public void Compute(TValue value)
    {
        this._capture!.Value = value;
    }
}
