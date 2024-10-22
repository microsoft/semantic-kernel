// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the options for a function choice behavior.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionChoiceBehaviorOptions
{
    /// <summary>Gets or sets whether multiple function invocations requested in parallel by the service may be invoked to run concurrently.</summary>
    /// <remarks>
    /// The default value is set to false. However, if the function invocations are safe to execute concurrently,
    /// such as when the function does not modify shared state, this setting can be set to true.
    /// </remarks>
    [JsonPropertyName("allow_concurrent_invocation")]
    public bool AllowConcurrentInvocation { get; set; } = false;
}
