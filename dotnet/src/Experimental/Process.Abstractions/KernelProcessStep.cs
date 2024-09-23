// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Process Step. Derive from this class to create a new Step for a Process.
/// </summary>
public class KernelProcessStep
{
    /// <inheritdoc/>
    public virtual ValueTask ActivateAsync(KernelProcessStepState state)
    {
        return default;
    }
}

/// <summary>
/// Process Step. Derive from this class to create a new Step with user-defined state of type TState for a Process.
/// </summary>
/// <typeparam name="TState">An instance of TState used for user-defined state.</typeparam>
public class KernelProcessStep<TState> : KernelProcessStep where TState : class, new()
{
    /// <inheritdoc/>
    public virtual ValueTask ActivateAsync(KernelProcessStepState<TState> state)
    {
        return default;
    }
}
