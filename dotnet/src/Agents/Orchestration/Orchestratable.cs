// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;

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
    /// <param name="handoff">The actor type used for handoff.  Only defined for nested orchestrations.</param>
    /// <param name="loggerFactory">The active logger factory.</param>
    /// <returns>A ValueTask containing the AgentType that indicates the registered agent.</returns>
    protected internal abstract ValueTask<AgentType> RegisterAsync(TopicId externalTopic, AgentType? handoff, ILoggerFactory loggerFactory);
}
