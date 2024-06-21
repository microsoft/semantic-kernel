// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

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
    [Experimental("SKEXP0010")]
    public static async IAsyncEnumerable<StreamingChatMessageContent> AddStreamingMessageAsync(this ChatHistory chatHistory, IAsyncEnumerable<AzureOpenAIStreamingChatMessageContent> streamingMessageContents)
    {
        List<StreamingChatMessageContent> messageContents = [];

        // Stream the response.
        StringBuilder? contentBuilder = null;
        Dictionary<int, string>? toolCallIdsByIndex = null;
        Dictionary<int, string>? functionNamesByIndex = null;
        Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex = null;
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

            AzureOpenAIFunctionToolCall.TrackStreamingToolingUpdate(chatMessage.ToolCallUpdate, ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);

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
                new AzureOpenAIChatMessageContent(
                    role,
                    contentBuilder?.ToString() ?? string.Empty,
                    messageContents[0].ModelId!,
                    AzureOpenAIFunctionToolCall.ConvertToolCallUpdatesToChatCompletionsFunctionToolCalls(ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex),
                    metadata)
                { AuthorName = streamedName });
        }
    }
}
