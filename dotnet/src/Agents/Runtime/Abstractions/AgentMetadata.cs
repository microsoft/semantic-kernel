// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Represents metadata associated with an agent, including its type, unique key, and description.
/// </summary>
public readonly struct AgentMetadata(string type, string key, string description) : IEquatable<AgentMetadata>
{
    /// <summary>
    /// An identifier that associates an agent with a specific factory function.
    /// Strings may only be composed of alphanumeric letters (a-z, 0-9), or underscores (_).
    /// </summary>
    public string Type { get; } = type;

    /// <summary>
    /// A unique key identifying the agent instance.
    /// Strings may only be composed of alphanumeric letters (a-z, 0-9), or underscores (_).
    /// </summary>
    public string Key { get; } = key;

    /// <summary>
    /// A brief description of the agent's purpose or functionality.
    /// </summary>
    public string Description { get; } = description;

    /// <inheritdoc/>
    public override readonly bool Equals(object? obj)
    {
        return obj is AgentMetadata agentMetadata && this.Equals(agentMetadata);
    }

    /// <inheritdoc/>
    public readonly bool Equals(AgentMetadata other)
    {
        return this.Type.Equals(other.Type, StringComparison.Ordinal) && this.Key.Equals(other.Key, StringComparison.Ordinal);
    }

    /// <inheritdoc/>
    public override readonly int GetHashCode()
    {
        return HashCode.Combine(this.Type, this.Key);
    }

    /// <inheritdoc/>
    public static bool operator ==(AgentMetadata left, AgentMetadata right)
    {
        return left.Equals(right);
    }

    /// <inheritdoc/>
    public static bool operator !=(AgentMetadata left, AgentMetadata right)
    {
        return !(left == right);
    }
}
