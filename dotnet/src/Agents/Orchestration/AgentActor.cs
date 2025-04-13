// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// An actor that represents an <see cref="Agents.Agent"/>.
/// </summary>
public abstract class AgentActor : PatternActor
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AgentActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agents.Agent"/>.</param>
    /// <param name="noThread">Option to automatically clean-up agent thread</param>
    protected AgentActor(AgentId id, IAgentRuntime runtime, Agent agent, bool noThread = false)
        : base(
            id,
            runtime,
            VerifyDescripion(agent),
            GetLogger(agent))
    {
        this.Agent = agent;
        this.NoThread = noThread;
    }

    /// <summary>
    /// Gets the associated agent.
    /// </summary>
    protected Agent Agent { get; }

    /// <summary>
    /// Gets a value indicating whether the agent thread should be removed after use.
    /// </summary>
    protected bool NoThread { get; }

    /// <summary>
    /// Gets or sets the current conversation thread used during agent communication.
    /// </summary>
    protected AgentThread? Thread { get; set; }

    /// <summary>
    /// Deletes the agent thread.
    /// </summary>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    protected async ValueTask DeleteThreadAsync(CancellationToken cancellationToken)
    {
        if (this.Thread != null)
        {
            await this.Thread.DeleteAsync(cancellationToken).ConfigureAwait(false);
            this.Thread = null;
        }
    }

    /// <summary>
    /// Invokes the agent with a single chat message.
    /// This method sets the message role to <see cref="AuthorRole.User"/> and delegates to the overload accepting multiple messages.
    /// </summary>
    /// <param name="input">The chat message content to send.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>A task that returns the response <see cref="ChatMessageContent"/>.</returns>
    protected ValueTask<ChatMessageContent> InvokeAsync(ChatMessageContent input, CancellationToken cancellationToken)
    {
        return this.InvokeAsync(new[] { input }, cancellationToken);
    }

    /// <summary>
    /// Invokes the agent with multiple chat messages.
    /// Processes the response items and consolidates the messages into a single <see cref="ChatMessageContent"/>.
    /// </summary>
    /// <param name="input">The list of chat messages to send.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>A task that returns the response <see cref="ChatMessageContent"/>.</returns>
    protected async ValueTask<ChatMessageContent> InvokeAsync(IList<ChatMessageContent> input, CancellationToken cancellationToken)
    {
        AgentResponseItem<ChatMessageContent>[] responses =
            await this.Agent.InvokeAsync(
                input,
                this.Thread,
                options: null,
                cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);

        AgentResponseItem<ChatMessageContent> response = responses[0];
        this.Thread ??= response.Thread;

        // The vast majority of responses will be a single message.  Responses with multiple messages will have their content merged.
        return new ChatMessageContent(response.Message.Role, string.Join("\n\n", responses.Select(response => response.Message)))
        {
            AuthorName = response.Message.AuthorName,
        };
    }

    /// <summary>
    /// Invokes the agent and streams chat message responses asynchronously.
    /// Yields each streaming message as it becomes available.
    /// </summary>
    /// <param name="input">The chat message content to send.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the stream.</param>
    /// <returns>An asynchronous stream of <see cref="StreamingChatMessageContent"/> responses.</returns>
    protected async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(ChatMessageContent input, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var responseStream = this.Agent.InvokeStreamingAsync(new[] { input }, this.Thread, options: null, cancellationToken);

        await foreach (AgentResponseItem<StreamingChatMessageContent> response in responseStream.ConfigureAwait(false))
        {
            if (this.NoThread)
            {
                // Do not block on thread clean-up
                Task task = this.DeleteThreadAsync(cancellationToken).AsTask();
            }
            {
                this.Thread ??= response.Thread;
            }
            yield return response.Message;
        }
    }

    private static string VerifyDescripion(Agent agent)
    {
        return agent.Description ?? throw new ArgumentException($"Missing agent description: {agent.Name ?? agent.Id}", nameof(agent));
    }

    private static ILogger GetLogger(Agent agent)
    {
        ILoggerFactory loggerFactory = agent.LoggerFactory ?? NullLoggerFactory.Instance;
        return loggerFactory.CreateLogger<AgentActor>();
    }
}
