// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Base abstractions for any actor that participates in an orchestration.
/// </summary>
public abstract class OrchestrationActor : BaseAgent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OrchestrationActor"/> class.
    /// </summary>
    protected OrchestrationActor(AgentId id, IAgentRuntime runtime, OrchestrationContext context, string description, ILogger? logger = null)
        : base(id, runtime, description, logger)
    {
        this.Context = context;
    }

    /// <summary>
    /// The orchestration context.
    /// </summary>
    protected OrchestrationContext Context { get; }

    /// <summary>
    /// Sends a message to a specified recipient agent-type through the runtime.
    /// </summary>
    /// <param name="message">The message object to send.</param>
    /// <param name="agentType">The recipient agent's type.</param>
    /// <param name="cancellationToken">A token used to cancel the operation if needed.</param>
    /// <returns>The agent identifier, if it exists.</returns>
    protected async ValueTask PublishMessageAsync(
        object message,
        AgentType agentType,
        CancellationToken cancellationToken = default)
    {
        await base.PublishMessageAsync(message, new TopicId(agentType), messageId: null, cancellationToken).ConfigureAwait(false);
    }
}
