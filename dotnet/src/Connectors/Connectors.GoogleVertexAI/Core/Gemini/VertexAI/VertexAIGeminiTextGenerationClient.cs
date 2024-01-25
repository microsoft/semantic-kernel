// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.VertexAI;

/// <summary>
/// Represents a client for interacting with the text generation gemini models by Vertex AI.
/// </summary>
internal sealed class VertexAIGeminiTextGenerationClient : IGeminiTextGenerationClient
{
    private readonly VertexAIGeminiChatCompletionClient _chatCompletionClient;

    /// <summary>
    /// Represents a client for interacting with the text generation gemini models by Vertex AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting text generation</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Response streaming json parser (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public VertexAIGeminiTextGenerationClient(
        HttpClient httpClient,
        string modelId,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
    {
        this._chatCompletionClient = new VertexAIGeminiChatCompletionClient(
            httpClient: httpClient,
            modelId: modelId,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            streamJsonParser: streamJsonParser,
            logger: logger);
    }

    // todo: temp solution due to gemini vertex ai (preview api) support only chat for now
    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var streamingChatMessageContent in this._chatCompletionClient.StreamGenerateChatMessageAsync(
                           new ChatHistory() { new(AuthorRole.User, prompt) }, executionSettings, cancellationToken))
        {
            yield return new StreamingTextContent(
                text: streamingChatMessageContent.Content,
                choiceIndex: streamingChatMessageContent.ChoiceIndex,
                modelId: streamingChatMessageContent.ModelId,
                encoding: streamingChatMessageContent.Encoding,
                metadata: streamingChatMessageContent.Metadata);
        }
    }

    // TODO: temp solution due to gemini vertex ai (preview api) support only streaming for now
    /// <inheritdoc/>
    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(prompt);
        var chatMessages = await this._chatCompletionClient
            .GenerateChatMessageAsync(chatHistory, executionSettings, cancellationToken)
            .ConfigureAwait(false);

        return chatMessages.Select(c => new TextContent(
            text: c.Content,
            modelId: c.ModelId,
            encoding: c.Encoding,
            metadata: c.Metadata)).ToList();
    }
}
