// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a <see cref="CancelKernelEventArgs"/> used in events just before a function is invoked.
/// </summary>
[Experimental("SKEXP0004")]
public sealed class FunctionInvokingEventArgs : CancelKernelEventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokingEventArgs"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this event is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    public FunctionInvokingEventArgs(KernelFunction function, KernelArguments arguments) :
        base(function, arguments, metadata: null)
    {
    }
}
