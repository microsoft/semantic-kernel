// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Azure;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Chat history extensions.
/// </summary>
public static class ChatHistoryExtensions
{
    /// <summary>
    /// Add a message to the chat history at the end of the streamed message
    /// </summary>
    /// <param name="chatHistory">Target chat history</param>
    /// <param name="streamingMessageContents"><see cref="IAsyncEnumerator{T}"/> list of streaming message contents</param>
    /// <returns>Returns the original streaming results with some message processing</returns>
    public static async IAsyncEnumerable<StreamingChatMessageContent> AddStreamingMessageAsync(this ChatHistory chatHistory, IAsyncEnumerable<AzureStreamingChatMessageContent> streamingMessageContents)
    {
        List<StreamingChatMessageContent> messageContents = new();

        // Stream the response.
        StringBuilder? contentBuilder = null;
        Dictionary<string, object?>? metadata = null;
        AuthorRole? streamedRole = null;
        string? streamedName = null;

        await foreach (var chatMessage in streamingMessageContents.ConfigureAwait(false))
        {
            metadata ??= (Dictionary<string, object?>?)chatMessage.Metadata;

            if (chatMessage.Content is { Length: > 0 } contentUpdate)
            {
                (contentBuilder ??= new()).Append(contentUpdate);
            }

            // Is always expected to have at least one chunk with the role provided from a streaming message
            streamedRole ??= chatMessage.Role;
            streamedName ??= chatMessage.AuthorName;

            messageContents.Add(chatMessage);
            yield return chatMessage;
        }

        if (messageContents.Count != 0)
        {
            var role = streamedRole ?? AuthorRole.Assistant;

            chatHistory.Add(
                new AzureChatMessageContent(
                    role,
                    contentBuilder?.ToString() ?? string.Empty,
                    messageContents[0].ModelId!,
                    metadata)
                { AuthorName = streamedName });
        }
    }
}
