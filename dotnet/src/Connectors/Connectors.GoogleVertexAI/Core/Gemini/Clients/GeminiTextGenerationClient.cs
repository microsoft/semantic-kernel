// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;

/// <summary>
/// Represents a client for interacting with the text generation gemini model.
/// </summary>
internal sealed class GeminiTextGenerationClient
{
    private readonly IGeminiChatCompletionClient _chatCompletionClient;

    /// <summary>
    /// Represents a client for interacting with the text generation gemini model.
    /// </summary>
    /// <param name="chatCompletionClient">A Gemini chat completion client instance.</param>
    internal GeminiTextGenerationClient(IGeminiChatCompletionClient chatCompletionClient)
    {
        this._chatCompletionClient = chatCompletionClient;
    }

    /// <summary>
    /// Generates text based on the given prompt asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>A list of text content generated based on the prompt.</returns>
    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        ChatHistory history = new();
        history.AddUserMessage(prompt);
        var resultMessages = await this._chatCompletionClient
            .GenerateChatMessageAsync(history, executionSettings, kernel, cancellationToken)
            .ConfigureAwait(false);

        return ConvertChatMessagesToTextContents(resultMessages);
    }

    /// <summary>
    /// Streams the generated text content asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingTextContent"/> streaming text contents.</returns>
    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        ChatHistory history = new();
        history.AddUserMessage(prompt);
        var resultMessages = this._chatCompletionClient
            .StreamGenerateChatMessageAsync(history, executionSettings, kernel, cancellationToken)
            .ConfigureAwait(false);

        await foreach (var chatMessage in resultMessages)
        {
            yield return ConvertStreamingChatMessageToStreamingTextContent(chatMessage);
        }
    }

    private static List<TextContent> ConvertChatMessagesToTextContents(IEnumerable<ChatMessageContent> resultMessages)
        => resultMessages.Select(chatMessage => new TextContent(
            text: chatMessage.Content,
            modelId: chatMessage.ModelId,
            innerContent: chatMessage,
            metadata: chatMessage.Metadata)).ToList();

    private static StreamingTextContent ConvertStreamingChatMessageToStreamingTextContent(StreamingChatMessageContent streamingChatMessage)
        => new(
            text: streamingChatMessage.Content,
            modelId: streamingChatMessage.ModelId,
            innerContent: streamingChatMessage,
            metadata: streamingChatMessage.Metadata,
            choiceIndex: ((GeminiMetadata)streamingChatMessage.Metadata!).Index);
}
