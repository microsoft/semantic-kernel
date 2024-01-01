#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Abstract;

internal interface IGeminiClient
{
    /// <summary>
    /// Gets the ID of the model.
    /// </summary>
    string? ModelId { get; }

    /// <summary>
    /// Gets the ID of the embedding model used for text embedding.
    /// </summary>
    string? EmbeddingModelId { get; }

    /// <summary>
    /// Generates text based on the given prompt asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>A list of text content generated based on the prompt.</returns>
    Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Streams the generated text content asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingTextContent"/> streaming text contents.</returns>
    IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);

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

    /// <summary>
    /// Generates embeddings for the given data asynchronously.
    /// </summary>
    /// <param name="data">The list of strings to generate embeddings for.</param>
    /// <param name="cancellationToken">The cancellation token to cancel the operation.</param>
    /// <returns>Result contains a list of read-only memories of floats representing the generated embeddings.</returns>
    Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Counts the number of tokens asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt to count tokens from.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>The number of tokens.</returns>
    Task<int> CountTokensAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);
}
