// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.

/// <summary>
/// Model for a connected agent to the assitant.
/// </summary>
public class AgentAssistantModel
{
    /// <summary>
    /// Gets or sets the Agent.
    /// </summary>
    public IAgent Agent { get; set; }

    /// <summary>
    /// Gets or sets the agent description for th assistant.
    /// </summary>
    public string Description { get; set; }

    /// <summary>
    /// Gets or sets the agent's input description for the assistant.
    /// </summary>
    public string InputDescription { get; set; }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
