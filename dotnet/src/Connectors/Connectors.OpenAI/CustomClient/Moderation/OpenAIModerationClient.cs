// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents a client for interacting with the openai moderation models.
/// </summary>
internal sealed class OpenAIModerationClient : CustomClientBase, IOpenAIModerationClient
{
    private readonly Uri _moderationEndpoint = new("https://api.openai.com/v1/moderations");

    private readonly string _modelId;

    /// <summary>
    /// Represents a client for interacting with the openai moderation models.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting moderation endpoint</param>
    /// <param name="httpRequestFactory">Request factory</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public OpenAIModerationClient(
        HttpClient httpClient,
        string modelId,
        IHttpRequestFactory httpRequestFactory,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            httpRequestFactory: httpRequestFactory,
            logger: logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this._modelId = modelId;
    }

    /// <inheritdoc/>
    public async Task<ClassificationContent> ClassifyTextAsync(
        string text,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(text);

        var geminiRequest = this.CreateRequest(text);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, this._moderationEndpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return ParseAndProcessClassificationResponse(body);
    }

    private static ClassificationContent ParseAndProcessClassificationResponse(string body)
        => GetClassificationContentFromResponse(DeserializeResponse<OpenAIModerationResponse>(body));

    private static ClassificationContent GetClassificationContentFromResponse(OpenAIModerationResponse response)
    {
        var moderationResult = response.Results[0];
        var classificationResult = new OpenAIClassificationResult(
            flagged: moderationResult.Flagged,
            entries: GetClassificationEntriesFromModerationResult(moderationResult));
        return new ClassificationContent(
            innerContent: response,
            result: classificationResult,
            modelId: response.ModelId,
            metadata: GetMetadataFromResponse(response));
    }

    private static Dictionary<string, object?> GetMetadataFromResponse(OpenAIModerationResponse response)
        => new() { ["Id"] = response.Id };

    private static List<OpenAIClassificationEntry> GetClassificationEntriesFromModerationResult(
        OpenAIModerationResponse.ModerationResult moderationResult)
    {
        var classificationEntries =
            from categoryWithFlag in moderationResult.CategoryFlags
            join categoryWithScore in moderationResult.CategoryScores on categoryWithFlag.Key equals categoryWithScore.Key
            select new OpenAIClassificationEntry(
                category: new OpenAIClassificationCategory(categoryWithFlag.Key),
                flagged: categoryWithFlag.Value,
                score: categoryWithScore.Value);
        return classificationEntries.ToList();
    }

    private OpenAIModerationRequest CreateRequest(string text)
        => OpenAIModerationRequest.FromText(text, this._modelId);
}
