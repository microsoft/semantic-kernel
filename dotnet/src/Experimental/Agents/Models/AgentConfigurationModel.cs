// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

/// <summary>
/// Represents a yaml configuration file for an agent.
/// </summary>
internal sealed class AgentConfigurationModel
{
    /// <summary>
    /// The agent name
    /// </summary>
    [YamlMember(Alias = "name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The agent description
    /// </summary>
    [YamlMember(Alias = "description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// The agent instructions template
    /// </summary>
    [YamlMember(Alias = "instructions")]
    public string Instructions { get; set; } = string.Empty;
}
