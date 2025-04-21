// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Defines a subscription that matches topics and maps them to agents.
/// </summary>
public interface ISubscriptionDefinition
{
    /// <summary>
    /// Gets the unique identifier of the subscription.
    /// </summary>
    string Id { get; }

    /// <summary>
    /// Determines whether the specified object is equal to the current subscription.
    /// </summary>
    /// <param name="obj">The object to compare with the current instance.</param>
    /// <returns><c>true</c> if the specified object is equal to this instance; otherwise, <c>false</c>.</returns>
    bool Equals([NotNullWhen(true)] object? obj);

    /// <summary>
    /// Determines whether the specified subscription is equal to the current subscription.
    /// </summary>
    /// <param name="other">The subscription to compare.</param>
    /// <returns><c>true</c> if the subscriptions are equal; otherwise, <c>false</c>.</returns>
    bool Equals(ISubscriptionDefinition? other);

    /// <summary>
    /// Returns a hash code for this subscription.
    /// </summary>
    /// <returns>A hash code for the subscription.</returns>
    int GetHashCode();

    /// <summary>
    /// Checks if a given <see cref="TopicId"/> matches the subscription.
    /// </summary>
    /// <param name="topic">The topic to check.</param>
    /// <returns><c>true</c> if the topic matches the subscription; otherwise, <c>false</c>.</returns>
    bool Matches(TopicId topic);

    /// <summary>
    /// Maps a <see cref="TopicId"/> to an <see cref="AgentId"/>.
    /// Should only be called if <see cref="Matches"/> returns <c>true</c>.
    /// </summary>
    /// <param name="topic">The topic to map.</param>
    /// <returns>The <see cref="AgentId"/> that should handle the topic.</returns>
    AgentId MapToAgent(TopicId topic);
}
