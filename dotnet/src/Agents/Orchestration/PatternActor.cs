// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// An actor that represents an <see cref="Agents.Agent"/>.
/// </summary>
public abstract class PatternActor : BaseAgent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PatternActor"/> class.
    /// </summary>
    protected PatternActor(AgentId id, IAgentRuntime runtime, string description, ILogger? logger = null)
        : base(id, runtime, description, logger)
    {
    }

    /// <summary>
    /// Sends a message to a specified recipient agent-type through the runtime.
    /// </summary>
    /// <param name="message">The message object to send.</param>
    /// <param name="agentType">The recipient agent's type.</param>
    /// <param name="cancellationToken">A token used to cancel the operation if needed.</param>
    protected async ValueTask SendMessageAsync(
        object message,
        AgentType agentType,
        CancellationToken cancellationToken = default)
    {
        AgentId? agentId = await this.GetAgentAsync(agentType, cancellationToken).ConfigureAwait(false);
        if (agentId.HasValue)
        {
            await this.SendMessageAsync(message, agentId.Value, messageId: null, cancellationToken).ConfigureAwait(false);
        }
    }
}
