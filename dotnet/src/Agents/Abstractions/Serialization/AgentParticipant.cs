// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// %%%
/// </summary>
internal sealed class AgentParticipant
{
    public string Id { get; init; } = string.Empty;

    public string? Name { get; init; }

    public string Type { get; init; } = string.Empty;

    [JsonConstructor]
    public AgentParticipant()
    {
    }

    public AgentParticipant(Agent agent)
    {
        this.Id = agent.Id;
        this.Name = agent.Name;
        this.Type = agent.GetType().FullName!;
    }
}
