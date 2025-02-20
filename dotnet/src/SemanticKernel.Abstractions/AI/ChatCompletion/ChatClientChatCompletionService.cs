// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
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
    public ChatClientChatCompletionService(IChatClient chatClient, IServiceProvider? serviceProvider)
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
        if (metadata?.ModelId is not null)
        {
            attrs[AIServiceExtensions.ModelIdKey] = metadata.ModelId;
        }
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes { get; }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatHistory);

        var messageList = ChatCompletionServiceExtensions.ToChatMessageList(chatHistory);
        var currentSize = messageList.Count;

        var completion = await this._chatClient.GetResponseAsync(
            messageList,
            executionSettings.ToChatOptions(kernel),
            cancellationToken).ConfigureAwait(false);

        chatHistory.AddRange(
            messageList
                .Skip(currentSize)
                .Select(m => ChatCompletionServiceExtensions.ToChatMessageContent(m)));

        return completion.Choices.Select(m => ChatCompletionServiceExtensions.ToChatMessageContent(m, completion)).ToList();
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatHistory);

        await foreach (var update in this._chatClient.GetStreamingResponseAsync(
            ChatCompletionServiceExtensions.ToChatMessageList(chatHistory),
            executionSettings.ToChatOptions(kernel),
            cancellationToken).ConfigureAwait(false))
        {
            yield return ToStreamingChatMessageContent(update);
        }
    }

    /// <summary>Converts a <see cref="ChatResponseUpdate"/> to a <see cref="StreamingChatMessageContent"/>.</summary>
    /// <remarks>This conversion should not be necessary once SK eventually adopts the shared content types.</remarks>
    private static StreamingChatMessageContent ToStreamingChatMessageContent(ChatResponseUpdate update)
    {
        StreamingChatMessageContent content = new(
            update.Role is not null ? new AuthorRole(update.Role.Value.Value) : null,
            null)
        {
            InnerContent = update.RawRepresentation,
            ChoiceIndex = update.ChoiceIndex,
            Metadata = update.AdditionalProperties,
            ModelId = update.ModelId
        };

        foreach (AIContent item in update.Contents)
        {
            StreamingKernelContent? resultContent =
                item is Microsoft.Extensions.AI.TextContent tc ? new Microsoft.SemanticKernel.StreamingTextContent(tc.Text) :
                item is Microsoft.Extensions.AI.FunctionCallContent fcc ?
                    new Microsoft.SemanticKernel.StreamingFunctionCallUpdateContent(fcc.CallId, fcc.Name, fcc.Arguments is not null ?
                        JsonSerializer.Serialize(fcc.Arguments!, AbstractionsJsonContext.Default.IDictionaryStringObject!) :
                        null) :
                null;

            if (resultContent is not null)
            {
                resultContent.ModelId = update.ModelId;
                content.Items.Add(resultContent);
            }
        }

        return content;
    }
}
