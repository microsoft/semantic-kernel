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
internal sealed class OpenAIModerationClient : CustomClientBase
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

    /// <summary>
    /// Classifies the given text using the openai moderation models.
    /// </summary>
    /// <param name="texts">Texts to classify.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>The results of the classification.</returns>
    public async Task<IReadOnlyList<ClassificationContent>> ClassifyTextsAsync(
        IEnumerable<string> texts,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(texts);
        var contents = texts.ToList();
        VerifyTextsAreNotNullOrWhiteSpace(contents);

        var geminiRequest = this.CreateRequest(contents);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, this._moderationEndpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return ParseAndProcessClassificationResponse(body, contents);
    }

    private static List<ClassificationContent> ParseAndProcessClassificationResponse(string body, List<string> contents)
        => GetClassificationContentFromResponse(DeserializeResponse<OpenAIModerationResponse>(body), contents);

    private static List<ClassificationContent> GetClassificationContentFromResponse(
        OpenAIModerationResponse response,
        List<string> contents)
    {
        ThrowIfResultsIsEmpty(response);
        return response.Results.Select((record, i)
            => GetClassificationContentFromResponseResult(response, record, contents[i])).ToList();
    }

    private static void ThrowIfResultsIsEmpty(OpenAIModerationResponse response)
    {
        if (response.Results.Count == 0)
        {
            throw new KernelException("No results returned from the OpenAI server.");
        }
    }

    private static ClassificationContent GetClassificationContentFromResponseResult(
        OpenAIModerationResponse response,
        OpenAIModerationResponse.ModerationResult result,
        string content)
    {
        var classificationResult = new OpenAIClassificationResult(
            flagged: result.Flagged,
            entries: GetClassificationEntriesFromModerationResult(result));
        return new ClassificationContent(
            innerContent: response,
            classifiedContent: content,
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

    private OpenAIModerationRequest CreateRequest(List<string> texts)
        => OpenAIModerationRequest.FromTexts(texts, this._modelId);

    private static void VerifyTextsAreNotNullOrWhiteSpace(List<string> contents)
    {
        if (contents.Any(string.IsNullOrWhiteSpace))
        {
            throw new ArgumentException("Texts cannot be null or empty or whitespace");
        }
    }
}
