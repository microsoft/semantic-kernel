// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

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
    [Experimental("SKEXP0014")]
    public static async IAsyncEnumerable<StreamingChatMessageContent> AddStreamingMessageAsync(this ChatHistory chatHistory, IAsyncEnumerable<OpenAIStreamingChatMessageContent> streamingMessageContents)
    {
        List<StreamingChatMessageContent> messageContents = new();
        // Stream the response.
        StringBuilder contentBuilder = new();
        List<ChatCompletionsFunctionToolCall>? functionCallResponses = null;
        Dictionary<string, object?>? metadata = null;
        AuthorRole? streamedRole = default;
        await foreach (var chatMessage in streamingMessageContents.ConfigureAwait(false))
        {
            if (metadata is null && chatMessage.Metadata is not null)
            {
                metadata = (Dictionary<string, object?>)chatMessage.Metadata;
            }

            if (chatMessage.Content is { Length: > 0 } contentUpdate)
            {
                contentBuilder.Append(contentUpdate);
            }

            if (chatMessage.ToolCallUpdate is ChatCompletionsFunctionToolCall functionToolCall)
            {
                if (functionToolCall.Id is not null &&
                    (functionCallResponses is not { Count: > 0 } || functionCallResponses[functionCallResponses.Count - 1].Id != functionToolCall.Id))
                {
                    // If this update has a tool ID and that ID is not the same as the last one we saw,
                    // add this as a new function call.
                    (functionCallResponses ??= new()).Add(functionToolCall);
                }
                else if (functionCallResponses is { Count: > 0 })
                {
                    // Augment the last function call with the new additional information.
                    ChatCompletionsFunctionToolCall last = functionCallResponses[functionCallResponses.Count - 1];
                    last.Name ??= functionToolCall.Name;
                    last.Arguments += functionToolCall.Arguments;
                }
            }

            // Is always expected to have at least one chunk with the role provided from a streaming message
            streamedRole ??= chatMessage.Role;

            messageContents.Add(chatMessage);
            yield return chatMessage;
        }

        if (messageContents.Count != 0)
        {
            chatHistory.AddMessage(new OpenAIChatMessageContent(
                streamedRole ?? AuthorRole.Assistant,
                contentBuilder.ToString(),
                messageContents[0].ModelId!,
                functionCallResponses ?? new List<ChatCompletionsFunctionToolCall>(),
                metadata));
        }
    }
}
