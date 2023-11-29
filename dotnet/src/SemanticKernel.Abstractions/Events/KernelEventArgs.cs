// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Base arguments for events.
/// </summary>
public abstract class KernelEventArgs : EventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelEventArgs"/> class.
    /// </summary>
    /// <param name="function">Kernel function</param>
    /// <param name="variables">Context variables related to the event</param>
    internal KernelEventArgs(KernelFunction function, ContextVariables variables)
    {
        Verify.NotNull(function);
        Verify.NotNull(variables);

        this.Function = function;
        this.Variables = variables;
        this.Metadata = new();
    }

    /// <summary>
    /// Kernel function
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Variables related to the event.
    /// </summary>
    public ContextVariables Variables { get; }

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata { get; protected set; }
}
