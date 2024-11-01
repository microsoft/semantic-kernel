﻿// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the options for a function choice behavior.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionChoiceBehaviorOptions
{
    /// <summary>
    /// Gets or sets whether AI model should prefer parallel function calls over sequential ones.
    /// If set to true, instructs the model to call multiple functions in one request if the model supports parallel function calls.
    /// Otherwise, it will send a request for each function call. If set to null, the AI model default value will be used.
    /// </summary>
    [JsonPropertyName("allow_parallel_calls")]
    public bool? AllowParallelCalls { get; set; } = null;

    /// <summary>
    /// Gets or sets whether multiple function invocations requested in parallel by the service may be invoked to run concurrently.
    /// </summary>
    /// <remarks>
    /// The default value is set to false. However, if the function invocations are safe to execute concurrently,
    /// such as when the function does not modify shared state, this setting can be set to true.
    /// </remarks>
    [JsonPropertyName("allow_concurrent_invocation")]
    public bool AllowConcurrentInvocation { get; set; } = false;
}
