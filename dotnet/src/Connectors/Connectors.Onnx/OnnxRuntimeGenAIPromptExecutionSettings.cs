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

    /// <summary>
    /// Top k tokens to sample from
    /// </summary>
    [JsonPropertyName("top_k")]
    public int? TopK { get; set; }

    /// <summary>
    /// Top p probability to sample with
    /// </summary>
    [JsonPropertyName("top_p")]
    public float? TopP { get; set; }

    /// <summary>
    /// Temperature to sample with
    /// </summary>
    [JsonPropertyName("temperature")]
    public float? Temperature { get; set; }

    /// <summary>
    /// Repetition penalty to sample with
    /// </summary>
    [JsonPropertyName("repetition_penalty")]
    public float? RepetitionPenalty { get; set; }

    /// <summary>
    /// The past/present kv tensors are shared and allocated once to max_length (cuda only)
    /// </summary>
    [JsonPropertyName("past_present_share_buffer")]
    public bool? PastPresentShareBuffer { get; set; }

    /// <summary>
    /// The number of independently computed returned sequences for each element in the batch
    /// </summary>
    [JsonPropertyName("num_return_sequences")]
    public int? NumReturnSequences { get; set; }

    /// <summary>
    /// The number of beams used during beam_search
    /// </summary>
    [JsonPropertyName("num_beams")]
    public int? NumBeams { get; set; }

    /// <summary>
    /// No repeated ngram in generated summaries
    /// </summary>
    [JsonPropertyName("no_repeat_ngram_size")]
    public int? NoRepeatNgramSize { get; set; }

    /// <summary>
    /// Min number of tokens to generate including the prompt
    /// </summary>
    [JsonPropertyName("min_tokens")]
    public int? MinTokens { get; set; }

    /// <summary>
    /// Max number of tokens to generate including the prompt
    /// </summary>
    [JsonPropertyName("max_tokens")]
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Length penalty of generated summaries
    /// </summary>
    [JsonPropertyName("length_penalty")]
    public float? LengthPenalty { get; set; }

    /// <summary>
    /// Indicating by which amount to penalize common words between beam group
    /// </summary>
    [JsonPropertyName("diversity_penalty")]
    public float? DiversityPenalty { get; set; }

    /// <summary>
    /// Allows the generation to stop early if all beam candidates reach the end token
    /// </summary>
    [JsonPropertyName("early_stopping")]
    public bool? EarlyStopping { get; set; }

    /// <summary>
    /// Do random sampling
    /// </summary>
    [JsonPropertyName("do_sample")]
    public bool? DoSample { get; set; }
}
