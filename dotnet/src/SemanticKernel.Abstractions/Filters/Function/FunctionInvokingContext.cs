// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to function before invocation.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionInvokingContext : FunctionFilterContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokingContext"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    public FunctionInvokingContext(KernelFunction function, KernelArguments arguments)
        : base(function, arguments, metadata: null)
    {
    }

    /// <summary>
    /// Gets or sets a value indicating whether the operation associated with
    /// the filter should be canceled.
    /// </summary>
    /// <remarks>
    /// The filter may set <see cref="Cancel"/> to true to indicate that the operation should
    /// be canceled. If there are multiple filters registered, subsequent filters
    /// may see and change a value set by a previous filter. The final result is what will
    /// be considered by the component that triggers filter.
    /// </remarks>
    public bool Cancel { get; set; }
}
