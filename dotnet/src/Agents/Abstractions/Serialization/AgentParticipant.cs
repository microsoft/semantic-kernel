// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// References an <see cref="Agent"/> instance participating in an <see cref="AgentChat"/>.
/// </summary>
public sealed class AgentParticipant
{
    /// <summary>
    /// Gets the captured <see cref="Agent.Id"/>.
    /// </summary>
    public string Id { get; init; } = string.Empty;

    /// <summary>
    /// Gets the captured <see cref="Agent.Name"/>.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Name { get; init; }

    /// <summary>
    /// Gets the fully qualified <see cref="Agent"/> type name.
    /// </summary>
    public string Type { get; init; } = string.Empty;

    /// <summary>
    /// Creates a new instance of <see cref="AgentParticipant"/>.
    /// </summary>
    /// <remarks>
    /// This parameterless constructor is for deserialization.
    /// </remarks>
    [JsonConstructor]
    public AgentParticipant() { }

    /// <summary>
    /// Creates a new instance of <see cref="AgentParticipant"/> with the specified agent.
    /// </summary>
    /// <remarks>
    /// This is a convenience constructor for serialization.
    /// </remarks>
    /// <param name="agent">The referenced <see cref="Agent"/>.</param>
    internal AgentParticipant(Agent agent)
    {
        this.Id = agent.Id;
        this.Name = agent.Name;
        this.Type = agent.GetType().FullName!;
    }
}
