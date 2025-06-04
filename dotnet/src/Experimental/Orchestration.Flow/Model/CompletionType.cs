// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Orchestration;

/// <summary>
/// The completion type of step
/// </summary>
public enum CompletionType
{
    /// <summary>
    /// Once
    /// </summary>
    Once,

    /// <summary>
    /// Optional
    /// </summary>
    Optional,

    /// <summary>
    /// At least once
    /// </summary>
    AtLeastOnce,

    /// <summary>
    /// Optional or multiple times
    /// </summary>
    ZeroOrMore,
}
