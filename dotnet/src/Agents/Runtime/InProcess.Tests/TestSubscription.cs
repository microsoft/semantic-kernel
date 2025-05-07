// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Runtime.InProcess.Tests;

public class TestSubscription(string topicType, string agentType, string? id = null) : ISubscriptionDefinition
{
    public string Id { get; } = id ?? Guid.NewGuid().ToString();

    public string TopicType { get; } = topicType;

    public AgentId MapToAgent(TopicId topic)
    {
        if (!this.Matches(topic))
        {
            throw new InvalidOperationException("TopicId does not match the subscription.");
        }

        return new AgentId(agentType, topic.Source);
    }

    public bool Equals(ISubscriptionDefinition? other) => this.Id == other?.Id;

    public override bool Equals([NotNullWhen(true)] object? obj) => obj is TestSubscription other && other.Equals(this);

    public override int GetHashCode() => this.Id.GetHashCode();

    public bool Matches(TopicId topic)
    {
        return topic.Type == this.TopicType;
    }
}
