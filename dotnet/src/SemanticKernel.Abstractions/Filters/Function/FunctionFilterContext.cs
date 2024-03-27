// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Base class with data related to function invocation.
/// </summary>
[Experimental("SKEXP0001")]
public abstract class FunctionFilterContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionFilterContext"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="metadata">A dictionary of metadata associated with the operation.</param>
    internal FunctionFilterContext(KernelFunction function, KernelArguments arguments, IReadOnlyDictionary<string, object?>? metadata)
    {
        Verify.NotNull(function);
        Verify.NotNull(arguments);

        this.Function = function;
        this.Arguments = arguments;
        this.Metadata = metadata;
    }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets the arguments associated with the operation.
    /// </summary>
    public KernelArguments Arguments { get; }

    /// <summary>
    /// Gets a dictionary of metadata associated with the operation.
    /// </summary>
    public IReadOnlyDictionary<string, object?>? Metadata { get; }
}
