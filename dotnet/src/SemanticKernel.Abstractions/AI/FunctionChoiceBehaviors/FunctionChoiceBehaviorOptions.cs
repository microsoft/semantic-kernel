// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the options for a function choice behavior.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionChoiceBehaviorOptions
{
    /// <summary>Gets or sets whether multiple function invocations requested in parallel by the service may be invoked to run concurrently.</summary>
    /// <remarks>
    /// The default is true. If the function invocations aren't safe to be invoked concurrently,
    /// such as if the function mutates shared state, this should be set to false.
    /// </remarks>
    public bool AllowConcurrentInvocation { get; set; } = true;
}
