// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Represents a <see cref="Agent"/> specialization based on OpenAI Response API.
/// </summary>
public sealed class OpenAIResponseAgent : Agent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIResponseAgent"/> class.
    /// </summary>
    /// <param name="client">The OpenAI provider for accessing the Responses API service.</param>
    public OpenAIResponseAgent(OpenAIResponseClient client)
    {
        Verify.NotNull(client);

        this.Client = client;
    }

    /// <summary>
    /// Expose client for additional use.
    /// </summary>
    public OpenAIResponseClient Client { get; }

    /// <summary>
    /// Storing of messages is enabled.
    /// </summary>
    public bool StoreEnabled { get; init; } = true;

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var agentThread = await this.EnsureThreadExistsWithMessagesAsync(messages, thread, cancellationToken).ConfigureAwait(false);

        // Invoke responses with the updated chat history.
        var chatHistory = new ChatHistory();
        chatHistory.AddRange(messages);
        var invokeResults = this.InternalInvokeAsync(
            this.Name,
            chatHistory,
            agentThread,
            options,
            cancellationToken);

        // Notify the thread of new messages and return them to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            await this.NotifyThreadOfNewMessage(agentThread, result, cancellationToken).ConfigureAwait(false);
            yield return new(result, agentThread);
        }
    }

    /// <inheritdoc/>
    public async override IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var agentThread = await this.EnsureThreadExistsWithMessagesAsync(messages, thread, cancellationToken).ConfigureAwait(false);

        // Invoke responses with the updated chat history.
        var chatHistory = new ChatHistory();
        chatHistory.AddRange(messages);
        int messageCount = chatHistory.Count;
        var invokeResults = this.InternalInvokeStreamingAsync(
            this.Name,
            chatHistory,
            agentThread,
            options,
            cancellationToken);

        // Return streaming chat message content to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            yield return new(result, agentThread);
        }

        // Notify the thread of new messages
        for (int i = messageCount; i < chatHistory.Count; i++)
        {
            await this.NotifyThreadOfNewMessage(agentThread, chatHistory[i], cancellationToken).ConfigureAwait(false);

            if (options?.OnIntermediateMessage is not null)
            {
                await options.OnIntermediateMessage(chatHistory[i]).ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        throw new NotImplementedException("API will be removed in a future release.");
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override IEnumerable<string> GetChannelKeys()
    {
        throw new NotImplementedException("API will be removed in a future release.");
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotImplementedException("API will be removed in a future release.");
    }

    #region private
    private async Task<AgentThread> EnsureThreadExistsWithMessagesAsync(ICollection<ChatMessageContent> messages, AgentThread? thread, CancellationToken cancellationToken)
    {
        if (this.StoreEnabled)
        {
            return await this.EnsureThreadExistsWithMessagesAsync(messages, thread, () => new OpenAIResponseAgentThread(this.Client), cancellationToken).ConfigureAwait(false);
        }

        return await this.EnsureThreadExistsWithMessagesAsync(messages, thread, () => new ChatHistoryAgentThread(), cancellationToken).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<ChatMessageContent> InternalInvokeAsync(
        string? agentName,
        ChatHistory history,
        AgentThread agentThread,
        AgentInvokeOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var kernel = options?.Kernel ?? this.Kernel;

        var overrideHistory = history;
        if (!this.StoreEnabled)
        {
            // Use the thread chat history
            overrideHistory = [.. this.GetChatHistory(agentThread), .. history];
        }

        var inputItems = overrideHistory.Select(c => c.ToResponseItem());
        var creationOptions = new ResponseCreationOptions()
        {
            EndUserId = this.GetDisplayName(),
            Instructions = $"{this.Instructions}\n{options?.AdditionalInstructions}",
            StoredOutputEnabled = this.StoreEnabled,
        };
        if (this.StoreEnabled && agentThread.Id != null)
        {
            creationOptions.PreviousResponseId = agentThread.Id;
        }

        var clientResult = await this.Client.CreateResponseAsync(inputItems, creationOptions, cancellationToken).ConfigureAwait(false);
        var response = clientResult.Value;

        if (this.StoreEnabled)
        {
            this.UpdateResponseId(agentThread, response.Id);
        }

        var messages = response.OutputItems.Select(o => o.ToChatMessageContent());

        foreach (ChatMessageContent message in messages)
        {
            message.AuthorName = this.Name;

            yield return message;
        }
    }

    private async IAsyncEnumerable<StreamingChatMessageContent> InternalInvokeStreamingAsync(
        string? agentName,
        ChatHistory history,
        AgentThread agentThread,
        AgentInvokeOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var kernel = options?.Kernel ?? this.Kernel;

        var overrideHistory = history;
        if (!this.StoreEnabled)
        {
            // Use the thread chat history
            overrideHistory = [.. this.GetChatHistory(agentThread), .. history];
        }

        var inputItems = overrideHistory.Select(c => c.ToResponseItem());
        var creationOptions = new ResponseCreationOptions()
        {
            EndUserId = this.GetDisplayName(),
            Instructions = $"{this.Instructions}\n{options?.AdditionalInstructions}",
            StoredOutputEnabled = this.StoreEnabled,
        };
        if (this.StoreEnabled && agentThread.Id != null)
        {
            creationOptions.PreviousResponseId = agentThread.Id;
        }

        await foreach (StreamingResponseUpdate update in this.Client.CreateResponseStreamingAsync(inputItems, creationOptions, cancellationToken).ConfigureAwait(false))
        {
            if (update is StreamingResponseOutputTextDeltaUpdate outputTextUpdate)
            {
                yield return outputTextUpdate.ToStreamingChatMessageContent();
            }
            else if (update is StreamingResponseCompletedUpdate responseCompletedUpdate)
            {
                if (this.StoreEnabled)
                {
                    this.UpdateResponseId(agentThread, responseCompletedUpdate.Response.Id);
                }
                foreach (var item in responseCompletedUpdate.Response.OutputItems)
                {
                    history.Add(item.ToChatMessageContent());
                }
            }
        }
    }

    private ChatHistory GetChatHistory(AgentThread agentThread)
    {
        if (agentThread is ChatHistoryAgentThread chatHistoryAgentThread)
        {
            return chatHistoryAgentThread.ChatHistory;
        }

        throw new InvalidOperationException("The agent thread is not a ChatHistoryAgentThread.");
    }

    private void UpdateResponseId(AgentThread agentThread, string id)
    {
        if (agentThread is OpenAIResponseAgentThread openAIResponseAgentThread)
        {
            openAIResponseAgentThread.ResponseId = id;
            return;
        }

        throw new InvalidOperationException("The agent thread is not an OpenAIResponseAgentThread.");
    }
    #endregion
}
