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
    private readonly MapResultState<TValue> _capture = new();

    /// <inheritdoc/>
    public override ValueTask ActivateAsync(KernelProcessStepState<MapResultState<TValue>> state)
    {
        state.State = this._capture;
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
