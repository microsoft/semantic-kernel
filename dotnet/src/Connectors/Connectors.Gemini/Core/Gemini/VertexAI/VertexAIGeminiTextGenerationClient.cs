#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.Gemini.VertexAI;

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
    /// <param name="configuration">Gemini configuration instance containing API key and other configuration options</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Response streaming json parser (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public VertexAIGeminiTextGenerationClient(
        HttpClient httpClient,
        GeminiConfiguration configuration,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
    {
        this._chatCompletionClient = new VertexAIGeminiChatCompletionClient(
            httpClient: httpClient,
            configuration: configuration,
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
        var contents =
            await this.StreamGenerateTextAsync(prompt, executionSettings, cancellationToken)
                .ToListAsync(cancellationToken).ConfigureAwait(false);

        return (from @group in contents.GroupBy(s => s.ChoiceIndex)
                let metadata = new GeminiMetadata()
                {
                    CandidatesTokenCount = ((GeminiMetadata)@group.Last().Metadata!).CandidatesTokenCount,
                    TotalTokenCount = ((GeminiMetadata)@group.Last().Metadata!).TotalTokenCount,
                    PromptTokenCount = ((GeminiMetadata)@group.Last().Metadata!).PromptTokenCount,
                    CurrentCandidateTokenCount = @group.Sum(s => ((GeminiMetadata)s.Metadata!).CurrentCandidateTokenCount),
                    FinishReason = ((GeminiMetadata)@group.Last().Metadata!).FinishReason,
                    Index = @group.Key,
                    PromptFeedbackBlockReason = ((GeminiMetadata)@group.First().Metadata!).PromptFeedbackBlockReason,
                    PromptFeedbackSafetyRatings = ((GeminiMetadata)@group.First().Metadata!).PromptFeedbackSafetyRatings,
                    ResponseSafetyRatings = ((GeminiMetadata)@group.Last().Metadata!).ResponseSafetyRatings,
                }
                select new TextContent(
                    text: @group.Aggregate(string.Empty, (s, content) => s += content.Text),
                    modelId: @group.First().ModelId,
                    encoding: @group.First().Encoding,
                    metadata: metadata))
            .ToList();
    }
}
