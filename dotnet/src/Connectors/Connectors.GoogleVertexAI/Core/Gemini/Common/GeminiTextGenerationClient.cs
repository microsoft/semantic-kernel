// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a client for interacting with the text generation gemini model.
/// </summary>
internal class GeminiTextGenerationClient : IGeminiTextGenerationClient
{
    private readonly IGeminiChatCompletionClient _chatCompletionClient;

    /// <summary>
    /// Represents a client for interacting with the text generation gemini model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting text generation</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Response streaming json parser (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiTextGenerationClient(
        HttpClient httpClient,
        string modelId,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this._chatCompletionClient = new GeminiChatCompletionClient(
            httpClient: httpClient,
            modelId: modelId,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            streamJsonParser: streamJsonParser,
            logger: logger);
    }

    internal GeminiTextGenerationClient(IGeminiChatCompletionClient chatCompletionClient)
    {
        this._chatCompletionClient = chatCompletionClient;
    }

    /// <inheritdoc/>
    public virtual async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        ChatHistory history = new();
        history.AddUserMessage(prompt);
        var resultMessages = await this._chatCompletionClient
            .GenerateChatMessageAsync(history, executionSettings, cancellationToken)
            .ConfigureAwait(false);

        return ConvertChatMessagesToTextContents(resultMessages);
    }

    /// <inheritdoc/>
    public virtual async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        ChatHistory history = new();
        history.AddUserMessage(prompt);
        var resultMessages = this._chatCompletionClient
            .StreamGenerateChatMessageAsync(history, executionSettings, cancellationToken)
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
