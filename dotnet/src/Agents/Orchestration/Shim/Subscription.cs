// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

internal sealed class Subscription(TopicId topic, string agentType, string? id = null) : ISubscriptionDefinition
{
    /// <inheritdoc/>
    public string Id { get; } = id ?? Guid.NewGuid().ToString();

    /// <summary>
    /// Gets the topic associated with the subscription.
    /// </summary>
    public TopicId Topic { get; } = topic;

    /// <inheritdoc/>
    public bool Equals(ISubscriptionDefinition? other) => this.Id == other?.Id;

    /// <inheritdoc/>
    public override int GetHashCode() => this.Id.GetHashCode();

    /// <inheritdoc/>
    public AgentId MapToAgent(TopicId topic)
    {
        if (!this.Matches(topic))
        {
            throw new InvalidOperationException("Topic does not match the subscription.");
        }

        return new AgentId(agentType, topic.Source);
    }

    /// <inheritdoc/>
    public bool Matches(TopicId topic) => this.Topic.Type == topic.Type;
}
