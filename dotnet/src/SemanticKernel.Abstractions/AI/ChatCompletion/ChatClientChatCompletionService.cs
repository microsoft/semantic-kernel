// Copyright (c) Microsoft. All rights reserved.

#if !UNITY
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>Provides an implementation of <see cref="IChatCompletionService"/> around an <see cref="IChatClient"/>.</summary>
internal sealed class ChatClientChatCompletionService : IChatCompletionService
{
    /// <summary>The wrapped <see cref="IChatClient"/>.</summary>
    private readonly IChatClient _chatClient;

    /// <summary>Initializes the <see cref="ChatClientChatCompletionService"/> for <paramref name="chatClient"/>.</summary>
    internal ChatClientChatCompletionService(IChatClient chatClient, IServiceProvider? serviceProvider)
    {
        Verify.NotNull(chatClient);

        // Store the client.
        this._chatClient = chatClient;

        // Initialize the attributes.
        var attrs = new Dictionary<string, object?>();
        this.Attributes = new ReadOnlyDictionary<string, object?>(attrs);

        var metadata = chatClient.GetService<ChatClientMetadata>();
        if (metadata?.ProviderUri is not null)
        {
            attrs[AIServiceExtensions.EndpointKey] = metadata.ProviderUri.ToString();
        }
        if (metadata?.DefaultModelId is not null)
        {
            attrs[AIServiceExtensions.ModelIdKey] = metadata.DefaultModelId;
        }
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes { get; }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatHistory);

        if (executionSettings is not null)
        {
            chatHistory = executionSettings.ChatClientPrepareChatHistoryForRequest(chatHistory);
        }

        var messageList = chatHistory.ToChatMessageList();
        var currentSize = messageList.Count;

        var completion = await this._chatClient.GetResponseAsync(
            messageList,
            executionSettings.ToChatOptions(kernel),
            cancellationToken).ConfigureAwait(false);

        if (completion.Messages.Count > 0)
        {
            // Add all but the last message into the chat history.
            for (int i = 0; i < completion.Messages.Count - 1; i++)
            {
                chatHistory.Add(completion.Messages[i].ToChatMessageContent(completion));
            }

            // Return the last message as the result.
            return [completion.Messages[completion.Messages.Count - 1].ToChatMessageContent(completion)];
        }

        return [];
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatHistory);

        if (executionSettings is not null)
        {
            chatHistory = executionSettings.ChatClientPrepareChatHistoryForRequest(chatHistory);
        }

        ChatRole? role = null;

        await foreach (var update in this._chatClient.GetStreamingResponseAsync(
            chatHistory.ToChatMessageList(),
            executionSettings.ToChatOptions(kernel),
            cancellationToken).ConfigureAwait(false))
        {
            role ??= update.Role;

            // Message tools and function calls should be individual messages in the history.
            foreach (var fcc in update.Contents.Where(c => c is Microsoft.Extensions.AI.FunctionCallContent or Microsoft.Extensions.AI.FunctionResultContent))
            {
                if (fcc is Microsoft.Extensions.AI.FunctionCallContent functionCallContent)
                {
                    chatHistory.Add(new ChatMessage(ChatRole.Assistant, [functionCallContent]).ToChatMessageContent());
                    continue;
                }

                if (fcc is Microsoft.Extensions.AI.FunctionResultContent functionResultContent)
                {
                    chatHistory.Add(new ChatMessage(ChatRole.Tool, [functionResultContent]).ToChatMessageContent());
                }
            }

            yield return update.ToStreamingChatMessageContent();
        }
    }
}
#endif
