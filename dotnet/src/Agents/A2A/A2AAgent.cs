// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
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
    /// <param name="client"><see cref="A2AClient"/> instance to associate with the agent.</param>
    /// <param name="agentCard"><see cref="AgentCard"/> instance associated ith the agent.</param>
    public A2AAgent(A2AClient client, AgentCard agentCard)
    {
        Verify.NotNull(client);
        Verify.NotNull(agentCard);

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
            requiresThreadRetrieval: false,
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
            requiresThreadRetrieval: false,
            cancellationToken).ConfigureAwait(false);

        // Invoke the agent.
        var chatMessages = new ChatHistory();
        var invokeResults = this.InternalInvokeStreamingAsync(
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
        throw new NotSupportedException($"{nameof(A2AAgent)} is not for use with {nameof(AgentChat)}.");
    }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        throw new NotSupportedException($"{nameof(A2AAgent)} is not for use with {nameof(AgentChat)}.");
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotSupportedException($"{nameof(A2AAgent)} is not for use with {nameof(AgentChat)}.");
    }

    #region private
    private async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InternalInvokeAsync(string name, ICollection<ChatMessageContent> messages, A2AAgentThread thread, AgentInvokeOptions options, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(messages);

        // Ensure all messages have the correct role.
        if (!messages.All(m => m.Role == AuthorRole.User))
        {
            throw new ArgumentException($"All messages must have the role {AuthorRole.User}.", nameof(messages));
        }

        // Send all messages to the remote agent in a single request.
        await foreach (var result in this.InvokeAgentAsync(messages, thread, options, cancellationToken).ConfigureAwait(false))
        {
            await this.NotifyThreadOfNewMessage(thread, result, cancellationToken).ConfigureAwait(false);
            yield return new(result, thread);
        }
    }

    private async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAgentAsync(ICollection<ChatMessageContent> messages, A2AAgentThread thread, AgentInvokeOptions options, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        List<Part> parts = [];
        foreach (var message in messages)
        {
            foreach (var item in message.Items)
            {
                if (item is TextContent textContent)
                {
                    parts.Add(new TextPart
                    {
                        Text = textContent.Text ?? string.Empty,
                    });
                }
                else
                {
                    throw new NotSupportedException($"Unsupported content type: {item.GetType().Name}. Only TextContent are supported.");
                }
            }
        }

        var messageSendParams = new MessageSendParams
        {
            Message = new Message
            {
                MessageId = Guid.NewGuid().ToString(),
                Role = MessageRole.User,
                Parts = parts,
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
                            textPart.Text),
                        thread);
                }
            }
        }
        else
        {
            throw new InvalidOperationException("Unexpected response type from A2A client.");
        }
    }

    private async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InternalInvokeStreamingAsync(ICollection<ChatMessageContent> messages, A2AAgentThread thread, AgentInvokeOptions options, ChatHistory chatMessages, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(messages);

        // Ensure all messages have the correct role.
        if (messages.Any(m => m.Role != AuthorRole.User))
        {
            throw new ArgumentException($"All messages must have the role {AuthorRole.User}.", nameof(messages));
        }

        // Send all messages to the remote agent in a single request.
        await foreach (var result in this.InvokeAgentAsync(messages, thread, options, cancellationToken).ConfigureAwait(false))
        {
            await this.NotifyThreadOfNewMessage(thread, result, cancellationToken).ConfigureAwait(false);
            yield return new(this.ToStreamingAgentResponseItem(result), thread);
        }
    }

    private AgentResponseItem<StreamingChatMessageContent> ToStreamingAgentResponseItem(AgentResponseItem<ChatMessageContent> responseItem)
    {
        var messageContent = new StreamingChatMessageContent(
            responseItem.Message.Role,
            responseItem.Message.Content,
            innerContent: responseItem.Message.InnerContent,
            modelId: responseItem.Message.ModelId,
            encoding: responseItem.Message.Encoding,
            metadata: responseItem.Message.Metadata);

        return new AgentResponseItem<StreamingChatMessageContent>(messageContent, responseItem.Thread);
    }
    #endregion
}
