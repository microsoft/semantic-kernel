// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines an agent.
/// </summary>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
public sealed class AgentDefinition
{
    /// <summary>
    /// Gets or sets the version of the schema being used.
    /// </summary>
    public string? Version { get; set; }

    /// <summary>
    /// Gets or sets the id of the deployed agent.
    /// </summary>
    public string? Id { get; set; }

    /// <summary>
    /// Gets or sets the type of the  agent.
    /// </summary>
    public string? Type { get; set; }

    /// <summary>
    /// Gets or sets the name of the  agent.
    /// </summary>
    public string? Name { get; set; }

    /// <summary>
    /// Gets or sets the description of the agent.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets the instructions for the agent to use.
    /// </summary>
    public string? Instructions { get; set; }

    /// <summary>
    /// Gets or sets the metadata associated with the agent.
    /// </summary>
    public IDictionary<string, object?>? Metadata { get; set; }

    /// <summary>
    /// Gets or sets the model used by the agent.
    /// </summary>
    public ModelDefinition? Model { get; set; }

    /// <summary>
    /// Gets or sets the collection of inputs used by the agent.
    /// </summary>
    public Dictionary<string, AgentInput>? Inputs { get; set; }

    /// <summary>
    /// Gets or sets the collection of outputs supported by the agent.
    /// </summary>
    public IList<AgentOutput>? Outputs { get; set; }

    /// <summary>
    /// Gets or sets the template options used by the agent.
    /// </summary>
    public TemplateOptions? Template { get; set; }

    /// <summary>
    /// Gets or sets the collection of tools used by the agent.
    /// </summary>
    public IList<AgentToolDefinition>? Tools { get; set; }
}
