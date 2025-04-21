// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.Agents.Runtime.Internal;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Agent ID uniquely identifies an agent instance within an agent runtime, including a distributed runtime.
/// It serves as the "address" of the agent instance for receiving messages.
/// </summary>\
/// <remarks>
/// See the Python equivalent:
/// <see href="https://github.com/microsoft/agent-runtime/blob/main/python/agent_runtime/core/agent_id.py">AgentId in AutoGen (Python)</see>.
/// </remarks>
[DebuggerDisplay($"AgentId(type=\"{{{nameof(Type)}}}\", key=\"{{{nameof(Key)}}}\")")]
public struct AgentId : IEquatable<AgentId>
{
    /// <summary>
    /// The default source value used when no source is explicitly provided.
    /// </summary>
    public const string DefaultKey = "default";

    private static readonly Regex KeyRegex = new(@"^[\x20-\x7E]+$", RegexOptions.Compiled); // ASCII 32-126

    /// <summary>
    /// An identifier that associates an agent with a specific factory function.
    /// Strings may only be composed of alphanumeric letters (a-z) and (0-9), or underscores (_).
    /// </summary>
    public string Type { get; }

    /// <summary>
    /// Agent instance identifier.
    /// Strings may only be composed of alphanumeric letters (a-z) and (0-9), or underscores (_).
    /// </summary>
    public string Key { get; }

    internal static Regex KeyRegex1 => KeyRegex2;

    internal static Regex KeyRegex2 => KeyRegex;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentId"/> struct.
    /// </summary>
    /// <param name="type">The agent type.</param>
    /// <param name="key">Agent instance identifier.</param>
    public AgentId(string type, string key)
    {
        AgentType.Validate(type);

        if (string.IsNullOrWhiteSpace(key) || !KeyRegex.IsMatch(key))
        {
            throw new ArgumentException($"Invalid AgentId key: '{key}'. Must only contain ASCII characters 32-126.");
        }

        this.Type = type;
        this.Key = key;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentId"/> struct from a tuple.
    /// </summary>
    /// <param name="kvPair">A tuple containing the agent type and key.</param>
    public AgentId((string Type, string Key) kvPair)
        : this(kvPair.Type, kvPair.Key)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentId"/> struct from an <see cref="AgentType"/>.
    /// </summary>
    /// <param name="type">The agent type.</param>
    /// <param name="key">Agent instance identifier.</param>
    public AgentId(AgentType type, string key)
        : this(type.Name, key)
    {
    }

    /// <summary>
    /// Convert a string of the format "type/key" into an <see cref="AgentId"/>.
    /// </summary>
    /// <param name="maybeAgentId">The agent ID string.</param>
    /// <returns>An instance of <see cref="AgentId"/>.</returns>
    public static AgentId FromStr(string maybeAgentId) => new(maybeAgentId.ToKeyValuePair(nameof(Type), nameof(Key)));

    /// <summary>
    /// Returns the string representation of the <see cref="AgentId"/>.
    /// </summary>
    /// <returns>A string in the format "type/key".</returns>
    public override readonly string ToString() => $"{this.Type}/{this.Key}";

    /// <summary>
    /// Determines whether the specified object is equal to the current <see cref="AgentId"/>.
    /// </summary>
    /// <param name="obj">The object to compare with the current instance.</param>
    /// <returns><c>true</c> if the specified object is equal to the current <see cref="AgentId"/>; otherwise, <c>false</c>.</returns>
    public override readonly bool Equals([NotNullWhen(true)] object? obj)
    {
        return (obj is AgentId other && this.Equals(other));
    }

    /// <inheritdoc/>
    public readonly bool Equals(AgentId other)
    {
        return this.Type == other.Type && this.Key == other.Key;
    }

    /// <summary>
    /// Returns a hash code for this <see cref="AgentId"/>.
    /// </summary>
    /// <returns>A hash code for the current instance.</returns>
    public override readonly int GetHashCode()
    {
        return HashCode.Combine(this.Type, this.Key);
    }

    /// <summary>
    /// Explicitly converts a string to an <see cref="AgentId"/>.
    /// </summary>
    /// <param name="id">The string representation of an agent ID.</param>
    /// <returns>An instance of <see cref="AgentId"/>.</returns>
    public static explicit operator AgentId(string id) => FromStr(id);

    /// <summary>
    /// Equality operator for <see cref="AgentId"/>.
    /// </summary>
    public static bool operator ==(AgentId left, AgentId right) => left.Equals(right);

    /// <summary>
    /// Inequality operator for <see cref="AgentId"/>.
    /// </summary>
    public static bool operator !=(AgentId left, AgentId right) => !left.Equals(right);
}
