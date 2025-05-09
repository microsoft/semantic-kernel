// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// An actor that represents an <see cref="Agents.Agent"/>.
/// </summary>
public abstract class AgentActor : OrchestrationActor
{
    private AgentInvokeOptions? _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="agent">An <see cref="Agents.Agent"/>.</param>
    /// <param name="logger">The logger to use for the actor</param>
    protected AgentActor(AgentId id, IAgentRuntime runtime, OrchestrationContext context, Agent agent, ILogger? logger = null)
        : base(
            id,
            runtime,
            context,
            VerifyDescription(agent),
            logger)
    {
        this.Agent = agent;
    }

    /// <summary>
    /// Gets the associated agent.
    /// </summary>
    protected Agent Agent { get; }

    /// <summary>
    /// Gets or sets the current conversation thread used during agent communication.
    /// </summary>
    protected AgentThread? Thread { get; set; }

    /// <summary>
    /// Optionally overridden to create custom invocation options for the agent.
    /// </summary>
    protected virtual AgentInvokeOptions? CreateInvokeOptions()
    {
        return null;
    }

    /// <summary>
    /// Optionally overridden to introduce customer filtering logic for the response callback.
    /// </summary>
    /// <param name="response">The agent response</param>
    /// <returns>true if the response should be filtered (hidden)</returns>
    protected virtual bool ResponseCallbackFilter(ChatMessageContent response) => false;

    /// <summary>
    /// Deletes the agent thread.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
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
        return this.InvokeAsync([input], cancellationToken);
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
        this.Context.Cancellation.ThrowIfCancellationRequested();

        AgentResponseItem<ChatMessageContent>[] responses =
            await this.Agent.InvokeAsync(
                input,
                this.Thread,
                this.GetInvokeOptions(),
                cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);

        AgentResponseItem<ChatMessageContent>? firstResponse = responses.FirstOrDefault();
        this.Thread ??= firstResponse?.Thread;

        // The vast majority of responses will be a single message.  Responses with multiple messages will have their content merged.
        ChatMessageContent response = new(firstResponse?.Message.Role ?? AuthorRole.Assistant, string.Join("\n\n", responses.Select(response => response.Message)))
        {
            AuthorName = firstResponse?.Message.AuthorName,
        };

        if (this.Context.ResponseCallback is not null && !this.ResponseCallbackFilter(response))
        {
            await this.Context.ResponseCallback.Invoke(response).ConfigureAwait(false);
        }

        return response;
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
        this.Context.Cancellation.ThrowIfCancellationRequested();

        var responseStream = this.Agent.InvokeStreamingAsync([input], this.Thread, this.GetInvokeOptions(), cancellationToken);

        await foreach (AgentResponseItem<StreamingChatMessageContent> response in responseStream.ConfigureAwait(false))
        {
            this.Thread ??= response.Thread;
            yield return response.Message;
        }
    }

    private AgentInvokeOptions? GetInvokeOptions() => this._options ??= this.CreateInvokeOptions();

    private static string VerifyDescription(Agent agent)
    {
        return agent.Description ?? throw new ArgumentException($"Missing agent description: {agent.Name ?? agent.Id}", nameof(agent));
    }
}
