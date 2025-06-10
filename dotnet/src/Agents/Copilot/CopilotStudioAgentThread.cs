// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Agents.CopilotStudio.Client;
using Microsoft.Agents.Core.Models;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Agents.Copilot;

/// <summary>
/// Represents a conversation thread for a <see cref="CopilotStudioAgent"/>.
/// </summary>
public sealed class CopilotStudioAgentThread : AgentThread
{
    private readonly CopilotClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="CopilotStudioAgentThread"/> class.
    /// </summary>
    /// <param name="client">A client used to interact with the Copilot Agent runtime service.</param>
    /// <param name="conversationId">An optional session Id to continue an existing session.</param>
    /// <exception cref="ArgumentNullException"></exception>
    public CopilotStudioAgentThread(CopilotClient client, string? conversationId = null)
    {
        this._client = client ?? throw new ArgumentNullException(nameof(client));
        this.Id = conversationId;
    }

    internal ILogger Logger { get; init; } = NullLogger.Instance;

    /// <inheritdoc />
    protected override async Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
    {
        try
        {
            await foreach (IActivity activity in this._client.StartConversationAsync(emitStartConversationEvent: true, cancellationToken).ConfigureAwait(false))
            {
                if (activity.Conversation is not null)
                {
                    return activity.Conversation.Id;
                }
            }

            return null;
        }
        catch (Exception exception)
        {
            throw new AgentThreadOperationException("The thread could not be created due to an unexpected error.", exception);
        }
    }

    /// <inheritdoc />
    protected override Task DeleteInternalAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogWarning($"{nameof(CopilotStudioAgent)} does not support thread deletion.");

        return Task.CompletedTask;
    }

    /// <inheritdoc />
    protected override async Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        // Create the thread if it does not exist.
        // Copilot agents cannot add messages to the thread without invoking so we don't do that here.
        await this.CreateAsync(cancellationToken).ConfigureAwait(false);
    }
}
