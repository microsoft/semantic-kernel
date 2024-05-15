// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace QualityCheckWithFilters.Models;

internal sealed class BertSummarizationEvaluationResponse
{
    [JsonPropertyName("precision")]
    public List<double> Precision { get; set; }

    [JsonPropertyName("recall")]
    public List<double> Recall { get; set; }

    [JsonPropertyName("f1")]
    public List<double> F1 { get; set; }
}

internal sealed class BleuSummarizationEvaluationResponse
{
    [JsonPropertyName("bleu")]
    public double Score { get; set; }

    [JsonPropertyName("precisions")]
    public List<double> Precisions { get; set; }

    [JsonPropertyName("brevity_penalty")]
    public double BrevityPenalty { get; set; }

    [JsonPropertyName("length_ratio")]
    public double LengthRatio { get; set; }
}

internal sealed class MeteorSummarizationEvaluationResponse
{
    [JsonPropertyName("meteor")]
    public double Score { get; set; }
}

internal sealed class CometTranslationEvaluationResponse
{
    [JsonPropertyName("scores")]
    public List<double> Scores { get; set; }

    [JsonPropertyName("system_score")]
    public double SystemScore { get; set; }
}
