// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

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
        switch (executionSettings)
        {
            case OnnxRuntimeGenAIPromptExecutionSettings settings:
                return settings;
            default:
                return new OnnxRuntimeGenAIPromptExecutionSettings();
        }
    }

    [JsonPropertyName("top_k")]
    public int TopK { get; set; } = 50;

    [JsonPropertyName("top_p")]
    public float TopP { get; set; } = 0.9f;

    [JsonPropertyName("temperature")]
    public float Temperature { get; set; } = 1;

    [JsonPropertyName("repetition_penalty")]
    public float RepetitionPenalty { get; set; } = 1;

    [JsonPropertyName("past_present_share_buffer")]
    public bool PastPresentShareBuffer { get; set; } = false;

    [JsonPropertyName("num_return_sequences")]
    public int NumReturnSequences { get; set; } = 1;

    [JsonPropertyName("num_beams")]
    public int NumBeams { get; set; } = 1;

    [JsonPropertyName("no_repeat_ngram_size")]
    public int NoRepeatNgramSize { get; set; } = 0;

    [JsonPropertyName("min_length")]
    public int MinLength { get; set; } = 0;

    [JsonPropertyName("max_length")]
    public int MaxLength { get; set; } = 200;

    [JsonPropertyName("length_penalty")]
    public float LengthPenalty { get; set; } = 1;

    [JsonPropertyName("diversity_penalty")]
    public float DiversityPenalty { get; set; } = 0;

    [JsonPropertyName("early_stopping")]
    public bool EarlyStopping { get; set; } = true;

    [JsonPropertyName("do_sample")]
    public bool DoSample { get; set; } = false;
}
