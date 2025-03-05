// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ChatWithAgent.ApiService.Config;

/// <summary>
/// Agent configuration.
/// </summary>
public sealed class AgentConfig
{
    /// <summary>
    /// Configuration section name.
    /// </summary>
    public const string ConfigSectionName = "Agent";

    /// <summary>
    /// Gets or sets the name of the agent.
    /// </summary>
    [Required]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the description of the agent.
    /// </summary>
    [Required]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the instructions for the agent.
    /// </summary>
    [Required]
    public string Instructions { get; set; } = string.Empty;
}
