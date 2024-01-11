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

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.VertexAI;

internal sealed class VertexAIGeminiClient : GeminiClient
{
    public VertexAIGeminiClient(
        HttpClient httpClient, GeminiConfiguration configuration,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
        : base(httpClient, configuration, httpRequestFactory, endpointProvider, streamJsonParser, logger) { }

    // todo: temp solution due to gemini vertex ai (preview api) support only chat for now
    public override async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var streamingChatMessageContent in this.StreamGenerateChatMessageAsync(
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
    public override async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
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

    // TODO: temp solution due to gemini vertex ai (preview api) support only streaming for now
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
                    content: @group.Aggregate(string.Empty, (s, content) => s += content.Content),
                    modelId: @group.First().ModelId,
                    encoding: @group.First().Encoding,
                    metadata: metadata))
            .ToList();
    }
}
