// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

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
    /// At least once
    /// </summary>
    AtLeastOnce,

    /// <summary>
    /// Optional or multiple times
    /// </summary>
    ZeroOrMore,
}
