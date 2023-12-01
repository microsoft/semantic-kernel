// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

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
    /// <param name="arguments">Kernel function arguments</param>
    internal KernelEventArgs(KernelFunction function, KernelArguments arguments)
    {
        Verify.NotNull(function);

        this.Function = function;
        this.Arguments = arguments;
        this.Metadata = new();
    }

    /// <summary>
    /// Kernel function
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Kernel function arguments.
    /// </summary>
    public KernelArguments Arguments { get; }

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata { get; protected set; }
}
