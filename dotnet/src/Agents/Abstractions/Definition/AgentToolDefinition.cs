// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// The options for defining a tool.
/// </summary>
[ExcludeFromCodeCoverage]
public sealed class AgentToolDefinition
{
    /// <summary>
    /// The type of the tool.
    /// </summary>
    /// <remarks>
    /// Used to identify which type of tool is being used e.g., code interpreter, openapi, ...
    /// </remarks>
    public string? Type { get; set; }

    /// <summary>
    /// The name of the tool.
    /// </summary>
    public string? Name { get; set; }

    /// <summary>
    /// Gets or sets the configuration for the tool.
    /// </summary>
    /// <remarks>
    /// Used to store tool specific configuration e.g., files associated with the tool, etc.
    /// </remarks>
    [JsonExtensionData]
    public IDictionary<string, object?>? Configuration { get; set; }
}
