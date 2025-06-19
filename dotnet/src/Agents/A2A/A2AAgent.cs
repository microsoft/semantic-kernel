// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using SharpA2A.Core;

namespace Microsoft.SemanticKernel.Agents.A2A;

/// <summary>
/// Provides a specialized <see cref="Agent"/> based on the A2A Protocol.
/// </summary>
public sealed class A2AAgent : Agent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="A2AAgent"/> class.
    /// </summary>
    /// <param name="client">A2AClient instance to associate with the agent.</param>
    /// <param name="agentCard">AgentCard instance associated ith the agent.</param>
    public A2AAgent(A2AClient client, AgentCard agentCard)
    {
        this.Client = client;
        this.AgentCard = agentCard;
        this.Name = agentCard.Name;
        this.Description = agentCard.Description;
    }

    /// <summary>
    /// The associated client.
    /// </summary>
    public A2AClient Client { get; }

    /// <summary>
    /// The associated agent card.
    /// </summary>
    public AgentCard AgentCard { get; }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var agentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new A2AAgentThread(this.Client),
            cancellationToken).ConfigureAwait(false);

        // Invoke the agent.
        var invokeResults = this.InternalInvokeAsync(
            this.AgentCard.Name,
            messages,
            agentThread,
            options ?? new AgentInvokeOptions(),
            cancellationToken);

        // Notify the thread of new messages and return them to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            await this.NotifyThreadOfNewMessage(agentThread, result, cancellationToken).ConfigureAwait(false);
            yield return new(result, agentThread);
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var agentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new A2AAgentThread(this.Client),
            cancellationToken).ConfigureAwait(false);

        // Invoke the agent.
        var chatMessages = new ChatHistory();
        var invokeResults = this.InternalInvokeStreamingAsync(
            this.AgentCard.Name,
            messages,
            agentThread,
            options ?? new AgentInvokeOptions(),
            chatMessages,
            cancellationToken);

        // Return the chunks to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            yield return new(result, agentThread);
        }

        // Notify the thread of any new messages that were assembled from the streaming response.
        foreach (var chatMessage in chatMessages)
        {
            await this.NotifyThreadOfNewMessage(agentThread, chatMessage, cancellationToken).ConfigureAwait(false);

            if (options?.OnIntermediateMessage is not null)
            {
                await options.OnIntermediateMessage(chatMessage).ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    #region private
    private async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InternalInvokeAsync(string name, ICollection<ChatMessageContent> messages, A2AAgentThread thread, AgentInvokeOptions options, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(messages);

        foreach (var message in messages)
        {
            await foreach (var result in this.InvokeAgentAsync(name, message, thread, options, cancellationToken).ConfigureAwait(false))
            {
                await this.NotifyThreadOfNewMessage(thread, result, cancellationToken).ConfigureAwait(false);
                yield return new(result, thread);
            }
        }
    }

    private async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAgentAsync(string name, ChatMessageContent message, A2AAgentThread thread, AgentInvokeOptions options, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var messageSendParams = new MessageSendParams
        {
            Message = new Message
            {
                MessageId = Guid.NewGuid().ToString(),
                Role = message.Role.ToMessageRole(),
                Parts =
                [
                    new TextPart
                    {
                        Text = message.Content! // TODO handle multiple items
                    }
                ]
            }
        };

        A2AResponse response = await this.Client.SendMessageAsync(messageSendParams).ConfigureAwait(false);
        if (response is AgentTask agentTask)
        {
            if (agentTask.Artifacts != null && agentTask.Artifacts.Count > 0)
            {
                foreach (var artifact in agentTask.Artifacts)
                {
                    foreach (var part in artifact.Parts)
                    {
                        if (part is TextPart textPart)
                        {
                            yield return new AgentResponseItem<ChatMessageContent>(new ChatMessageContent(AuthorRole.Assistant, textPart.Text), thread);
                        }
                    }
                }
                Console.WriteLine();
            }
        }
        else if (response is Message messageResponse)
        {
            foreach (var part in messageResponse.Parts)
            {
                if (part is TextPart textPart)
                {
                    yield return new AgentResponseItem<ChatMessageContent>(
                        new ChatMessageContent(
                            AuthorRole.Assistant,
                            textPart.Text,
                            encoding: message.Encoding,
                            metadata: message.Metadata),
                        thread);
                }
            }
        }
        else
        {
            throw new InvalidOperationException("Unexpected response type from A2A client.");
        }
    }

    private IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InternalInvokeStreamingAsync(string name, ICollection<ChatMessageContent> messages, A2AAgentThread thread, AgentInvokeOptions options, ChatHistory chatMessages, CancellationToken cancellationToken)
    {
        Verify.NotNull(messages);

        throw new NotImplementedException();
    }
    #endregion
}
