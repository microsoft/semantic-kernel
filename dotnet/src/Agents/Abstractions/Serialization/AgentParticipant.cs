// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// References an <see cref="Agent"/> instance participating in an <see cref="AgentChat"/>.
/// </summary>
public sealed class AgentParticipant
{
    /// <summary>
    /// The captured <see cref="Agent.Id"/>.
    /// </summary>
    public string Id { get; init; } = string.Empty;

    /// <summary>
    /// The captured <see cref="Agent.Name"/>.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Name { get; init; }

    /// <summary>
    /// The fully qualified <see cref="Agent"/> type name.
    /// </summary>
    public string Type { get; init; } = string.Empty;

    /// <summary>
    /// Parameterless constructor for deserialization.
    /// </summary>
    [JsonConstructor]
    public AgentParticipant() { }

    /// <summary>
    /// Convenience constructor for serialization.
    /// </summary>
    /// <param name="agent">The referenced <see cref="Agent"/></param>
    internal AgentParticipant(Agent agent)
    {
        this.Id = agent.Id;
        this.Name = agent.Name;
        this.Type = agent.GetType().FullName!;
    }
}
