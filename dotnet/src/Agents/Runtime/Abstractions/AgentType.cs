// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Represents the type of an agent as a string.
/// This is a strongly-typed wrapper around a string, ensuring type safety when working with agent types.
/// </summary>
/// <remarks>
/// This struct is immutable and provides implicit conversion to and from <see cref="string"/>.
/// </remarks>
public readonly partial struct AgentType : IEquatable<AgentType>
{
#if NET
    [GeneratedRegex("^[a-zA-Z_][a-zA-Z0-9_]*$")]
    private static partial Regex TypeRegex();
#else
    private static Regex TypeRegex() => new("^[a-zA-Z_][a-zA-Z0-9_]*$", RegexOptions.Compiled);
#endif

    internal static void Validate(string type)
    {
        if (string.IsNullOrWhiteSpace(type) || !TypeRegex().IsMatch(type))
        {
            throw new ArgumentException($"Invalid AgentId type: '{type}'. Must be alphanumeric (a-z, 0-9, _) and cannot start with a number or contain spaces.");
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentId"/> struct.
    /// </summary>
    /// <param name="type">The agent type.</param>
    public AgentType(string type)
    {
        Validate(type);
        this.Name = type;
    }

    /// <summary>
    /// The string representation of this agent type.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// Returns the string representation of the <see cref="AgentType"/>.
    /// </summary>
    /// <returns>A string in the format "type/source".</returns>
    public override readonly string ToString() => this.Name;

    /// <summary>
    /// Explicitly converts a <see cref="Type"/> to an <see cref="AgentType"/>.
    /// </summary>
    /// <param name="type">The .NET <see cref="Type"/> to convert.</param>
    /// <returns>An <see cref="AgentType"/> instance with the name of the provided type.</returns>
    public static explicit operator AgentType(Type type) => new(type.Name);

    /// <summary>
    /// Implicitly converts a <see cref="string"/> to an <see cref="AgentType"/>.
    /// </summary>
    /// <param name="type">The string representation of the agent type.</param>
    /// <returns>An <see cref="AgentType"/> instance with the given name.</returns>
    public static implicit operator AgentType(string type) => new(type);

    /// <summary>
    /// Implicitly converts an <see cref="AgentType"/> to a <see cref="string"/>.
    /// </summary>
    /// <param name="type">The <see cref="AgentType"/> instance.</param>
    /// <returns>The string representation of the agent type.</returns>
    public static implicit operator string(AgentType type) => type.ToString();

    /// <inheritdoc/>
    public override bool Equals(object? obj)
    {
        return obj is AgentType other && this.Equals(other);
    }

    /// <inheritdoc/>
    public bool Equals(AgentType other)
    {
        return this.Name.Equals(other.Name, StringComparison.Ordinal);
    }

    /// <inheritdoc/>
    public override int GetHashCode()
    {
        return this.Name.GetHashCode();
    }

    /// <inheritdoc/>
    public static bool operator ==(AgentType left, AgentType right)
    {
        return left.Equals(right);
    }

    /// <inheritdoc/>
    public static bool operator !=(AgentType left, AgentType right)
    {
        return !(left == right);
    }
}
