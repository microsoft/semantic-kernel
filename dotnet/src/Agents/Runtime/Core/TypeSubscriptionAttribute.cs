// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core;

/// <summary>
/// Specifies that the attributed class subscribes to a particular topic for agent message handling.
/// </summary>
/// <param name="topic">The topic identifier that this class subscribes to.</param>
[AttributeUsage(AttributeTargets.Class)]
public sealed class TypeSubscriptionAttribute(string topic) : Attribute
{
    /// <summary>
    /// Gets the topic identifier associated with this subscription.
    /// </summary>
    public string Topic => topic;

    /// <summary>
    /// Creates a subscription definition that binds the topic to the specified agent type.
    /// </summary>
    /// <param name="agentType">The agent type to bind to this topic.</param>
    /// <returns>An <see cref="ISubscriptionDefinition"/> representing the binding.</returns>
    internal ISubscriptionDefinition Bind(AgentType agentType)
    {
        return new TypeSubscription(this.Topic, agentType);
    }
}
