// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// The inner step type of an event listener step.
/// </summary>
public sealed class KernelProcessEventListenerStep : KernelProcessStep
{
    /// <summary>
    /// Handle events sent to the listener.
    /// </summary>
    [KernelFunction]
    public void HandleEvent()
    {
    }
}
