// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgentRuntime.Model;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Agents.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="BedrockAgent"/>.
/// </summary>
public class BedrockAgentChannel : AgentChannel<BedrockAgent>
{
    private readonly ChatHistory _history = [];

    private const string MessagePlaceholder = "[SILENCE]";

    /// <summary>
    /// Receive messages from a group chat.
    /// Bedrock requires the chat history to alternate between user and agent messages.
    /// Thus, when receiving messages, the message sequence will be mutated by inserting
    /// placeholder agent or user messages as needed.
    /// </summary>
    /// <param name="history">The history of messages to receive.</param>
    /// <param name="cancellationToken">A token to monitor for cancellation requests.</param>
    protected override Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        foreach (var incomingMessage in history)
        {
            if (string.IsNullOrEmpty(incomingMessage.Content))
            {
                this.Logger.LogWarning("Received a message with no content. Skipping.");
                continue;
            }

            if (this._history.Count == 0 || this._history.Last().Role != incomingMessage.Role)
            {
                this._history.Add(incomingMessage);
            }
            else
            {
                this._history.Add
                (
                    new ChatMessageContent
                    (
                        incomingMessage.Role == AuthorRole.Assistant ? AuthorRole.User : AuthorRole.Assistant,
                        MessagePlaceholder
                    )
                );
                this._history.Add(incomingMessage);
            }
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    protected override async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        BedrockAgent agent,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (!this.PrepareAndValidateHistory())
        {
            yield break;
        }

        InvokeAgentRequest invokeAgentRequest = new()
        {
            AgentAliasId = BedrockAgent.WorkingDraftAgentAlias,
            AgentId = agent.Id,
            SessionId = BedrockAgent.CreateSessionId(),
            InputText = this._history.Last().Content,
            SessionState = this.ParseHistoryToSessionState(),
        };
        await foreach (ChatMessageContent message in agent.InvokeAsync(invokeAgentRequest, null, null, cancellationToken).ConfigureAwait(false))
        {
            if (message.Content is not null)
            {
                this._history.Add(message);
                // All messages from Bedrock agents are user facing, i.e., function calls are not returned as messages
                yield return (true, message);
            }
        }
    }

    /// <inheritdoc/>
    protected override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        BedrockAgent agent,
        IList<ChatMessageContent> messages,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (!this.PrepareAndValidateHistory())
        {
            yield break;
        }

        InvokeAgentRequest invokeAgentRequest = new()
        {
            AgentAliasId = BedrockAgent.WorkingDraftAgentAlias,
            AgentId = agent.Id,
            SessionId = BedrockAgent.CreateSessionId(),
            InputText = this._history.Last().Content,
            SessionState = this.ParseHistoryToSessionState(),
        };
        await foreach (StreamingChatMessageContent message in agent.InvokeStreamingAsync(invokeAgentRequest, null, null, cancellationToken).ConfigureAwait(false))
        {
            if (message.Content is not null)
            {
                this._history.Add(new()
                {
                    Role = AuthorRole.Assistant,
                    Content = message.Content,
                    AuthorName = message.AuthorName,
                    InnerContent = message.InnerContent,
                    ModelId = message.ModelId,
                });
                // All messages from Bedrock agents are user facing, i.e., function calls are not returned as messages
                yield return message;
            }
        }
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return this._history.ToDescendingAsync();
    }

    /// <inheritdoc/>
    protected override Task ResetAsync(CancellationToken cancellationToken)
    {
        this._history.Clear();

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    protected override string Serialize()
        => JsonSerializer.Serialize(ChatMessageReference.Prepare(this._history));

    #region private methods

    private bool PrepareAndValidateHistory()
    {
        if (this._history.Count == 0)
        {
            this.Logger.LogWarning("No messages to send. Bedrock requires at least one message to start a conversation.");
            return false;
        }

        this.EnsureHistoryAlternates();
        this.EnsureLastMessageIsUser();
        if (string.IsNullOrEmpty(this._history.Last().Content))
        {
            this.Logger.LogWarning("Last message has no content. Bedrock doesn't support empty messages.");
            return false;
        }

        return true;
    }

    private void EnsureHistoryAlternates()
    {
        if (this._history.Count <= 1)
        {
            return;
        }

        int currentIndex = 1;
        while (currentIndex < this._history.Count)
        {
            if (this._history[currentIndex].Role == this._history[currentIndex - 1].Role)
            {
                this._history.Insert(
                    currentIndex,
                    new ChatMessageContent(
                        this._history[currentIndex].Role == AuthorRole.Assistant ? AuthorRole.User : AuthorRole.Assistant,
                        MessagePlaceholder
                    )
                );
                currentIndex += 2;
            }
            else
            {
                currentIndex++;
            }
        }
    }

    private void EnsureLastMessageIsUser()
    {
        if (this._history.Count > 0 && this._history.Last().Role != AuthorRole.User)
        {
            this._history.Add(new ChatMessageContent(AuthorRole.User, MessagePlaceholder));
        }
    }

    private SessionState ParseHistoryToSessionState()
    {
        SessionState sessionState = new();

        // We don't take the last message as it needs to be sent separately in another parameter.
        if (this._history.Count > 1)
        {
            sessionState.ConversationHistory = new()
            {
                Messages = []
            };

            foreach (var message in this._history.Take(this._history.Count - 1))
            {
                if (message.Content is null)
                {
                    throw new InvalidOperationException("Message content cannot be null.");
                }
                if (message.Role != AuthorRole.Assistant && message.Role != AuthorRole.User)
                {
                    throw new InvalidOperationException("Message role must be either Assistant or User.");
                }

                sessionState.ConversationHistory.Messages.Add(new()
                {
                    Role = message.Role == AuthorRole.Assistant
                        ? Amazon.BedrockAgentRuntime.ConversationRole.Assistant
                        : Amazon.BedrockAgentRuntime.ConversationRole.User,
                    Content = [
                        new Amazon.BedrockAgentRuntime.Model.ContentBlock()
                        {
                            Text = message.Content,
                        },
                    ],
                });
            }
        }

        return sessionState;
    }
    #endregion
}
