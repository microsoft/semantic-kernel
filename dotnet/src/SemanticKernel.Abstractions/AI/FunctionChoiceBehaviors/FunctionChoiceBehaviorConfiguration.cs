// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represent function choice behavior configuration.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionChoiceBehaviorConfiguration
{
    /// <summary>
    /// Represents an AI model's decision-making strategy for calling functions.
    /// </summary>
    public FunctionChoice Choice { get; init; }

    /// <summary>
    /// The functions available for AI model.
    /// </summary>
    public IEnumerable<KernelFunction>? Functions { get; init; }

    /// <summary>
    /// Indicates whether the functions should be automatically invoked by the AI service/connector.
    /// </summary>
    public bool AutoInvoke { get; init; } = true;

    /// <summary>
    /// Number of requests that are part of a single user interaction that should include this functions in the request.
    /// </summary>
    /// <remarks>
    /// Once this limit is reached, the functions will no longer be included in subsequent requests that are part of the user operation, e.g.
    /// if this is 1, the first request will include the functions, but the subsequent response sending back the functions' result
    /// will not include the functions for further use.
    /// </remarks>
    public int? MaximumUseAttempts { get; init; }

    /// <summary>
    /// Specifies whether validation against a specified list of functions is required before allowing the model to request a function from the kernel.
    /// </summary>
    public bool? AllowAnyRequestedKernelFunction { get; init; }
}
