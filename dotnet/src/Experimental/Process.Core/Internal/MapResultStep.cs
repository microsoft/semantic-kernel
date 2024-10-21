// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// The step state for capturing the result of a map operation.
/// </summary>
internal sealed record MapResultState
{
    /// <summary>
    /// The result of the map operation.
    /// </summary>
    public object? Value { get; set; }
};

/// <summary>
/// Step whose sole responsibility is to capture the result of a map operation.
/// </summary>
/// <remarks>
/// Limits assumptions regarding the shape of the actual map operation.
/// </remarks>
internal sealed class MapResultStep : KernelProcessStep<MapResultState>
{
    private MapResultState? _capture;

    /// <inheritdoc/>
    public override ValueTask ActivateAsync(KernelProcessStepState<MapResultState> state)
    {
        this._capture = state.State;
        return default;
    }

    /// <summary>
    /// Function for capturing the result of a map operation.
    /// </summary>
    [KernelFunction]
    public void Compute(object value)
    {
        this._capture ??= new();

        this._capture.Value = value;
    }
}
