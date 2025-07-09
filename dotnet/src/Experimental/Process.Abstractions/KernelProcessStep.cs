// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Process Step. Derive from this class to create a new Step for a Process.
/// </summary>
public class KernelProcessStep
{
    /// <summary>
    /// Class containing events related to the step. This class is used to define events that can be raised during the execution of a step in a process.
    /// This class should contain only public static readonly <see cref="KernelProcessEventDescriptor"/> components.<br/>
    /// When using in a custom step, it should be overwritten with:
    /// <code>
    /// public static new class StepEvents
    /// {
    ///     ...custom step events described with KernelProcessEventDescriptor...
    /// }
    /// </code>
    /// </summary>
    public static class StepEvents
    {
    }

    /// <summary>
    /// Name of the step given by the StepBuilder id.
    /// </summary>
    public string? StepName { get; init; }

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
