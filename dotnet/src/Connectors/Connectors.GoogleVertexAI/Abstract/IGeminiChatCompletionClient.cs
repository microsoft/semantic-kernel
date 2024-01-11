#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;

internal interface IGeminiChatCompletionClient
{
    /// <summary>
    /// Generates a chat message asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>Returns a list of chat message contents.</returns>
    Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Generates a stream of chat messages asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingChatMessageContent"/> streaming chat contents.</returns>
    IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);
}
