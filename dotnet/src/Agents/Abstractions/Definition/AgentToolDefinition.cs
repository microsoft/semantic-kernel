// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// The options for defining a tool.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class AgentToolDefinition
{
    /// <summary>
    /// The id of the tool.
    /// </summary>
    /// <remarks>
    /// This is typically a short string, but can be any string that is compatible with the agent.
    /// The id is used to identify the tool in the agent and must be unique in the collection of tools.
    /// </remarks>
    public string? Id { get; set; }

    /// <summary>
    /// The type of the tool.
    /// </summary>
    /// <remarks>
    /// Used to identify which type of tool is being used e.g., code interpreter, openapi, ...
    /// </remarks>
    public string? Type { get; set; }

    /// <summary>
    /// The description of the tool.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets the options for the tool.
    /// </summary>
    /// <remarks>
    /// Used to store tool specific options e.g., files associated with the tool, etc.
    /// </remarks>
    [JsonExtensionData]
    public IDictionary<string, object?>? Options { get; set; }
}
