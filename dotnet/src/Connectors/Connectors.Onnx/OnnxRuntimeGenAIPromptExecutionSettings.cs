// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

/// <summary>
/// OnnxRuntimeGenAI Execution Settings.
/// </summary>
public sealed class OnnxRuntimeGenAIPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Convert PromptExecutionSettings to OnnxRuntimeGenAIPromptExecutionSettings
    /// </summary>
    /// <param name="executionSettings"></param>
    /// <returns></returns>
    public static OnnxRuntimeGenAIPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new OnnxRuntimeGenAIPromptExecutionSettings();
        }

        if (executionSettings is OnnxRuntimeGenAIPromptExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var onnxRuntimeGenAIPromptExecutionSettings = JsonSerializer.Deserialize<OnnxRuntimeGenAIPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        return onnxRuntimeGenAIPromptExecutionSettings!;
    }

    [JsonPropertyName("top_k")]
    public int? TopK { get; set; }

    [JsonPropertyName("top_p")]
    public float? TopP { get; set; }

    [JsonPropertyName("temperature")]
    public float? Temperature { get; set; }

    [JsonPropertyName("repetition_penalty")]
    public float? RepetitionPenalty { get; set; }

    [JsonPropertyName("past_present_share_buffer")]
    public bool? PastPresentShareBuffer { get; set; }

    [JsonPropertyName("num_return_sequences")]
    public int? NumReturnSequences { get; set; }

    [JsonPropertyName("num_beams")]
    public int? NumBeams { get; set; }

    [JsonPropertyName("no_repeat_ngram_size")]
    public int? NoRepeatNgramSize { get; set; }

    [JsonPropertyName("min_tokens")]
    public int? MinTokens { get; set; }

    [JsonPropertyName("max_tokens")]
    public int? MaxTokens { get; set; }

    [JsonPropertyName("length_penalty")]
    public float? LengthPenalty { get; set; }

    [JsonPropertyName("diversity_penalty")]
    public float? DiversityPenalty { get; set; }

    [JsonPropertyName("early_stopping")]
    public bool? EarlyStopping { get; set; }

    [JsonPropertyName("do_sample")]
    public bool? DoSample { get; set; }
}
