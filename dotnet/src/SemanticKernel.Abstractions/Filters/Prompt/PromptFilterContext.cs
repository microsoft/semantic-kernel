// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

public abstract class PromptFilterContext
{
    internal PromptFilterContext(KernelFunction function, KernelArguments arguments, IDictionary<string, object?>? metadata)
    {
        Verify.NotNull(function);
        Verify.NotNull(arguments);

        this.Function = function;
        this.Arguments = arguments;
        this.Metadata = metadata;
    }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this event is associated.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets the arguments associated with the operation.
    /// </summary>
    public KernelArguments Arguments { get; }

    /// <summary>
    /// Gets a dictionary of metadata related to the event.
    /// </summary>
    public IDictionary<string, object?>? Metadata { get; }
}
