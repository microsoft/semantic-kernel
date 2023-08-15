// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments context available to the Kernel.Running event.
/// </summary>
public sealed class KernelRunningEventArgs : CancelEventArgs
{
    internal KernelRunningEventArgs(SKContext context, string? prompt)
    {
        Verify.NotNull(context);

        this.SKContext = context;
        this.Prompt = prompt;
    }

    /// <summary>
    /// Current SKContext prior to executing the function.
    /// </summary>
    public SKContext SKContext { get; }

    /// <summary>
    /// Prompt that was generated prior to sending to the LLM.
    /// </summary>
    /// <remarks>
    /// May be null for native functions.
    /// </remarks>
    public string? Prompt { get; }
}
