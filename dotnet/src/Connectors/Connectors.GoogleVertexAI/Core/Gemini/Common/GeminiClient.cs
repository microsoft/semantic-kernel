#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Linq;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.Common;

internal abstract class GeminiClient : ClientBase
{
    protected GeminiClient(
        HttpClient httpClient,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            logger: logger) { }

    protected static GeminiRequest CreateGeminiRequest(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(geminiExecutionSettings.MaxTokens);
        var geminiRequest = GeminiRequest.FromPromptAndExecutionSettings(prompt, geminiExecutionSettings);
        return geminiRequest;
    }

    protected static GeminiMetadata GetResponseMetadata(
        GeminiResponse geminiResponse,
        GeminiResponseCandidate candidate) => new()
    {
        FinishReason = candidate.FinishReason,
        Index = candidate.Index,
        PromptTokenCount = geminiResponse.UsageMetadata?.PromptTokenCount ?? 0,
        CurrentCandidateTokenCount = candidate.TokenCount,
        CandidatesTokenCount = geminiResponse.UsageMetadata?.CandidatesTokenCount ?? 0,
        TotalTokenCount = geminiResponse.UsageMetadata?.TotalTokenCount ?? 0,
        PromptFeedbackBlockReason = geminiResponse.PromptFeedback?.BlockReason,
        PromptFeedbackSafetyRatings = geminiResponse.PromptFeedback?.SafetyRatings.ToList(),
        ResponseSafetyRatings = candidate.SafetyRatings.ToList(),
    };

    protected void LogUsageMetadata(GeminiMetadata metadata)
    {
        this.Logger.LogDebug(
            "Gemini usage metadata: Candidates tokens: {CandidatesTokens}, Prompt tokens: {PromptTokens}, Total tokens: {TotalTokens}",
            metadata.CandidatesTokenCount,
            metadata.PromptTokenCount,
            metadata.TotalTokenCount);
    }
}
