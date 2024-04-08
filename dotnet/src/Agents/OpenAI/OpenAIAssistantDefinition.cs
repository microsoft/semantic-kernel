// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// $$$
/// </summary>
public sealed class OpenAIAssistantDefinition
{
    /// <summary>
    /// $$$
    /// </summary>
    public string? Model { get; init; }

    /// <summary>
    /// $$$
    /// </summary>
    public string? Description { get; init; }

    ///// <summary>
    ///// $$$
    ///// </summary>
    //public string? Id { get; init; } $$$

    /// <summary>
    /// $$$
    /// </summary>
    public string? Instructions { get; init; }

    /// <summary>
    /// $$$
    /// </summary>
    public string? Name { get; init; }

    /// <summary>
    /// $$$
    /// </summary>
    public bool EnableCodeIntepreter { get; init; }

    /// <summary>
    /// $$$
    /// </summary>
    public bool EnableRetrieval { get; init; }

    /// <summary>
    /// $$$
    /// </summary>
    public IEnumerable<string>? FileIds { get; init; }

    /// <summary>
    /// $$$
    /// </summary>
    public IDictionary<string, string>? Metadata { get; init; }
}
