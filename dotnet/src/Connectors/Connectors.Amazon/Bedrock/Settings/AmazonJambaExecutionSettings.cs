// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Prompt execution settings for AI21 Jamba Chat Completion
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public class AmazonJambaExecutionSettings : PromptExecutionSettings
{
    private float? _temperature;
    private float? _topP;
    private int? _maxTokens;
    private List<string>? _stop;
    private int? _n;
    private double? _frequencyPenalty;
    private double? _presencePenalty;

    /// <summary>
    /// How much variation to provide in each answer. Setting this value to 0 guarantees the same response to the same question every time. Setting a higher value encourages more variation. Modifies the distribution from which tokens are sampled. Default: 1.0, Range: 0.0 – 2.0
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
    /// Limit the pool of next tokens in each step to the top N percentile of possible tokens, where 1.0 means the pool of all possible tokens, and 0.01 means the pool of only the most likely next tokens.
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
    /// The maximum number of tokens to allow for each generated response message. Typically, the best way to limit output length is by providing a length limit in the system prompt (for example, "limit your answers to three sentences"). Default: 4096, Range: 0 – 4096.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    public int? MaxTokens
    {
        get => this._maxTokens;
        set
        {
            this.ThrowIfFrozen();
            this._maxTokens = value;
        }
    }

    /// <summary>
    /// End the message when the model generates one of these strings. The stop sequence is not included in the generated message. Each sequence can be up to 64K long, and can contain newlines as \n characters.
    /// </summary>
    [JsonPropertyName("stop")]
    public List<string>? Stop
    {
        get => this._stop;
        set
        {
            this.ThrowIfFrozen();
            this._stop = value;
        }
    }

    /// <summary>
    /// How many responses to generate (one for text generation).
    /// </summary>
    [JsonPropertyName("n")]
    public int? NumberOfResponses
    {
        get => this._n;
        set
        {
            this.ThrowIfFrozen();
            this._n = value;
        }
    }

    /// <summary>
    /// Reduce frequency of repeated words within a single response message by increasing this number. This penalty gradually increases the more times a word appears during response generation. Setting to 2.0 will produce a string with few, if any repeated words.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    public double? FrequencyPenalty
    {
        get => this._frequencyPenalty;
        set
        {
            this.ThrowIfFrozen();
            this._frequencyPenalty = value;
        }
    }

    /// <summary>
    /// Reduce the frequency of repeated words within a single message by increasing this number. Unlike frequency penalty, presence penalty is the same no matter how many times a word appears.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    public double? PresencePenalty
    {
        get => this._presencePenalty;
        set
        {
            this.ThrowIfFrozen();
            this._presencePenalty = value;
        }
    }

    /// <summary>
    /// Converts PromptExecutionSettings to AmazonJambaChatExecutionSettings
    /// </summary>
    /// <param name="executionSettings">The Kernel standard PromptExecutionSettings.</param>
    /// <returns>Model specific execution settings</returns>
    public static AmazonJambaExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AmazonJambaExecutionSettings();
            case AmazonJambaExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<AmazonJambaExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}
