// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core;

/// <summary>
/// Specifies that the attributed class subscribes to topics based on a type prefix.
/// </summary>
/// <param name="topic">The topic prefix used for matching incoming messages.</param>
[AttributeUsage(AttributeTargets.Class)]
public sealed class TypePrefixSubscriptionAttribute(string topic) : Attribute
{
    /// <summary>
    /// Gets the topic prefix that this subscription listens for.
    /// </summary>
    public string Topic => topic;

    /// <summary>
    /// Creates a subscription definition that binds the topic to the specified agent type.
    /// </summary>
    /// <param name="agentType">The agent type to bind to this topic.</param>
    /// <returns>An <see cref="ISubscriptionDefinition"/> representing the binding.</returns>
    internal ISubscriptionDefinition Bind(AgentType agentType)
    {
        return new TypePrefixSubscription(this.Topic, agentType);
    }
}
