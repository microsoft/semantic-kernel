// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Prompt execution settings for Anthropic Claude Text Generation
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class AmazonClaudeExecutionSettings : PromptExecutionSettings
{
    private int _maxTokensToSample;
    private List<string>? _stopSequences;
    private float? _temperature;
    private float? _topP;
    private int? _topK;

    /// <summary>
    /// Default max tokens for a text generation.
    /// </summary>
    private const int DefaultTextMaxTokens = 200;

    /// <summary>
    /// (Required) The maximum number of tokens to generate before stopping. We recommend a limit of 4,000 tokens for optimal performance.
    /// </summary>
    [JsonPropertyName("max_tokens_to_sample")]
    public int MaxTokensToSample
    {
        get => this._maxTokensToSample;
        set
        {
            this.ThrowIfFrozen();
            this._maxTokensToSample = value;
        }
    }

    /// <summary>
    /// (Optional) Sequences that will cause the model to stop generating. Anthropic Claude models stop on "\n\nHuman:", and may include additional built-in stop sequences in the future.Use the stop_sequences inference parameter to include additional strings that will signal the model to stop generating text.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    public List<string>? StopSequences
    {
        get => this._stopSequences;
        set
        {
            this.ThrowIfFrozen();
            this._stopSequences = value;
        }
    }

    /// <summary>
    /// (Optional) The amount of randomness injected into the response. Use a value closer to 0 for analytical / multiple choice, and a value closer to 1 for creative and generative tasks.
    /// </summary>
    [JsonPropertyName("temperature")]
    public float? Temperature
    {
        get => this._temperature;
        set
        {
            this.ThrowIfFrozen();
            this._temperature = value;
        }
    }

    /// <summary>
    /// (Optional) Use nucleus sampling. In nucleus sampling, Anthropic Claude computes the cumulative distribution over all the options for each subsequent token in decreasing probability order and cuts it off once it reaches a particular probability specified by top_p.You should alter either temperature or top_p, but not both.
    /// </summary>
    [JsonPropertyName("top_p")]
    public float? TopP
    {
        get => this._topP;
        set
        {
            this.ThrowIfFrozen();
            this._topP = value;
        }
    }

    /// <summary>
    /// (Optional) Only sample from the top K options for each subsequent token. Use top_k to remove long tail low probability responses.
    /// </summary>
    [JsonPropertyName("top_k")]
    public int? TopK
    {
        get => this._topK;
        set
        {
            this.ThrowIfFrozen();
            this._topK = value;
        }
    }

    /// <summary>
    /// Converts PromptExecutionSettings to ClaudeExecutionSettings
    /// </summary>
    /// <param name="executionSettings">The Kernel standard PromptExecutionSettings.</param>
    /// <returns>Model specific execution settings.</returns>
    public static AmazonClaudeExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AmazonClaudeExecutionSettings { MaxTokensToSample = DefaultTextMaxTokens };
            case AmazonClaudeExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<AmazonClaudeExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}
