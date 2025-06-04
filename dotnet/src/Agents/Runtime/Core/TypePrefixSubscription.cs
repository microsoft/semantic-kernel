// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core;

/// <summary>
/// This subscription matches on topics based on a prefix of the type and maps to agents using the source of the topic as the agent key.
/// This subscription causes each source to have its own agent instance.
/// </summary>
/// <remarks>
/// Example:
/// <code>
/// var subscription = new TypePrefixSubscription("t1", "a1");
/// </code>
/// In this case:
/// - A <see cref="TopicId"/> with type `"t1"` and source `"s1"` will be handled by an agent of type `"a1"` with key `"s1"`.
/// - A <see cref="TopicId"/> with type `"t1"` and source `"s2"` will be handled by an agent of type `"a1"` with key `"s2"`.
/// - A <see cref="TopicId"/> with type `"t1SUFFIX"` and source `"s2"` will be handled by an agent of type `"a1"` with key `"s2"`.
/// </remarks>
public class TypePrefixSubscription : ISubscriptionDefinition
{
    /// <summary>
    /// Initializes a new instance of the <see cref="TypePrefixSubscription"/> class.
    /// </summary>
    /// <param name="topicTypePrefix">Topic type prefix to match against.</param>
    /// <param name="agentType">Agent type to handle this subscription.</param>
    /// <param name="id">Unique identifier for the subscription. If not provided, a new UUID will be generated.</param>
    public TypePrefixSubscription(string topicTypePrefix, AgentType agentType, string? id = null)
    {
        this.TopicTypePrefix = topicTypePrefix;
        this.AgentType = agentType;
        this.Id = id ?? Guid.NewGuid().ToString();
    }

    /// <summary>
    /// Gets the unique identifier of the subscription.
    /// </summary>
    public string Id { get; }

    /// <summary>
    /// Gets the topic type prefix used for matching.
    /// </summary>
    public string TopicTypePrefix { get; }

    /// <summary>
    /// Gets the agent type that handles this subscription.
    /// </summary>
    public AgentType AgentType { get; }

    /// <summary>
    /// Checks if a given <see cref="TopicId"/> matches the subscription based on its type prefix.
    /// </summary>
    /// <param name="topic">The topic to check.</param>
    /// <returns><c>true</c> if the topic's type starts with the subscription's prefix, <c>false</c> otherwise.</returns>
    public bool Matches(TopicId topic)
    {
        return topic.Type.StartsWith(this.TopicTypePrefix, StringComparison.Ordinal);
    }

    /// <summary>
    /// Maps a <see cref="TopicId"/> to an <see cref="AgentId"/>. Should only be called if <see cref="Matches"/> returns true.
    /// </summary>
    /// <param name="topic">The topic to map.</param>
    /// <returns>An <see cref="AgentId"/> representing the agent that should handle the topic.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the topic does not match the subscription.</exception>
    public AgentId MapToAgent(TopicId topic)
    {
        if (!this.Matches(topic))
        {
            throw new InvalidOperationException("TopicId does not match the subscription.");
        }

        return new AgentId(this.AgentType, topic.Source); // No need for .Name, since AgentType implicitly converts to string
    }

    /// <summary>
    /// Determines whether the specified object is equal to the current subscription.
    /// </summary>
    /// <param name="obj">The object to compare with the current instance.</param>
    /// <returns><c>true</c> if the specified object is equal to this instance; otherwise, <c>false</c>.</returns>
    public override bool Equals([NotNullWhen(true)] object? obj)
    {
        return
            obj is TypePrefixSubscription other &&
                (this.Id == other.Id ||
                    (this.AgentType == other.AgentType &&
                     this.TopicTypePrefix == other.TopicTypePrefix));
    }

    /// <summary>
    /// Determines whether the specified subscription is equal to the current subscription.
    /// </summary>
    /// <param name="other">The subscription to compare.</param>
    /// <returns><c>true</c> if the subscriptions are equal; otherwise, <c>false</c>.</returns>
    public bool Equals(ISubscriptionDefinition? other) => this.Id == other?.Id;

    /// <summary>
    /// Returns a hash code for this instance.
    /// </summary>
    /// <returns>A hash code for this instance, suitable for use in hashing algorithms and data structures.</returns>
    public override int GetHashCode()
    {
        return HashCode.Combine(this.Id, this.AgentType, this.TopicTypePrefix);
    }
}
