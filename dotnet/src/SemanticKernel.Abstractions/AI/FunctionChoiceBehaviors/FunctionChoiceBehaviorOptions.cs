// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the options for a function choice behavior.
/// </summary>
public sealed class FunctionChoiceBehaviorOptions
{
    /// <summary>
    /// Indicates whether the functions should be automatically invoked by the AI service/connector.
    /// </summary>
    public bool AutoInvoke { get; set; } = true;
}
