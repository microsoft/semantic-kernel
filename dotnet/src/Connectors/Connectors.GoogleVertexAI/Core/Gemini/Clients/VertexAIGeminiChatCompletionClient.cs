// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a client for interacting with the chat completion gemini models by Vertex AI.
/// </summary>
// todo: remove this class when gemini vertex ai (preview api) support non-streaming
internal sealed class VertexAIGeminiChatCompletionClient : GeminiChatCompletionClient
{
    /// <summary>
    /// Represents a client for interacting with the chat completion gemini models by Vertex AI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Response streaming json parser (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public VertexAIGeminiChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            modelId: modelId,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            streamJsonParser: streamJsonParser,
            logger: logger)
    { }

    // TODO: temp solution due to gemini vertex ai (preview api) support only streaming for now
    /// <inheritdoc/>
    public override async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        var contents =
            await this.StreamGenerateChatMessageAsync(chatHistory, executionSettings, cancellationToken)
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
                select new ChatMessageContent(
                    role: @group.First().Role ?? AuthorRole.Assistant,
                    content: @group.Aggregate(string.Empty, (s, content) => s + content.Content),
                    modelId: @group.First().ModelId,
                    encoding: @group.First().Encoding,
                    metadata: metadata))
            .ToList();
    }
}
