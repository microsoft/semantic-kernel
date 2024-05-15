// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace QualityCheckWithFilters.Models;

internal class EvaluationRequest
{
    [JsonPropertyName("sources")]
    public List<string> Sources { get; set; }
}

internal sealed class SummarizationEvaluationRequest : EvaluationRequest
{
    [JsonPropertyName("summaries")]
    public List<string> Summaries { get; set; }
}

internal sealed class TranslationEvaluationRequest : EvaluationRequest
{
    [JsonPropertyName("translations")]
    public List<string> Translations { get; set; }
}
