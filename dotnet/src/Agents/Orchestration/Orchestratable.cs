// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Common protocol for <see cref="AgentOrchestration{TInput, TSource, TResult, TOutput}"/> so it
/// can be utlized by an another orchestration.
/// </summary>
public abstract class Orchestratable
{
    /// <summary>
    /// Registers the orchestratable component with the external system using a specified topic and an optional target actor.
    /// </summary>
    /// <param name="externalTopic">The topic identifier to be used for registration.</param>
    /// <param name="targetActor">An optional target actor type, if applicable, that may influence registration behavior.</param>
    /// <returns>A ValueTask containing the AgentType that indicates the registered agent.</returns>
    protected internal abstract ValueTask<AgentType> RegisterAsync(TopicId externalTopic, AgentType? targetActor);
}
