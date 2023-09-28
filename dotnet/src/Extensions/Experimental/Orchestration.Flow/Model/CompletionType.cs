// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130

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
