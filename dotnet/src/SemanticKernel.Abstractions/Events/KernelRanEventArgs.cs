// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments context available to the Kernel.Ran event.
/// </summary>
public sealed class KernelRanEventArgs : EventArgs
{
    internal KernelRanEventArgs(SKContext context)
    {
        Verify.NotNull(context);

        this.SKContext = context;
    }

    /// <summary>
    /// Current SKContext changes after the function was executed.
    /// </summary>
    public SKContext SKContext { get; }
}
