// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

/// <summary>
/// Request settings for Claude.
/// </summary>
public class AnthropicRequestSettings : AIRequestSettings
{
    private int _maxTokensToSample = 256;
    private readonly List<string> _stopSequences = new();
    private double? _temperature = 1.0;
    private double? _topP;
    private int? _topK;

    /// <summary>
    /// The maximum number of tokens to generate before stopping.
    /// </summary>
    /// <remarks>
    /// Note that our models may stop before reaching this maximum. This parameter only specifies the absolute maximum
    /// number of tokens to generate.
    /// </remarks>
    [JsonPropertyName("max_tokens_to_sample")]
    public int MaxTokensToSample
    {
        get => this._maxTokensToSample;
        set
        {
            if (value < 1) throw new ArgumentOutOfRangeException(nameof(value), value, "MaxTokensToSample must be greater than zero.");
            this._maxTokensToSample = value;
        }
    }

    /// <summary>
    /// Sequences that will cause the model to stop generating completion text.
    /// </summary>
    /// <remarks>
    /// Our models stop on "\n\nHuman:", and may include additional built-in stop sequences in the future. By providing
    /// the stop_sequences parameter, you may include additional strings that will cause the model to stop generating.
    /// </remarks>
    [JsonPropertyName("stop_sequences")]
    public IList<string> StopSequences
    {
        get => this._stopSequences;
        set
        {
            this._stopSequences.Clear();
            this._stopSequences.AddRange(value);
        }
    }

    /// <summary>
    /// Amount of randomness injected into the response.
    /// </summary>
    /// <remarks>
    /// Defaults to 1. Ranges from 0 to 1. Use temp closer to 0 for analytical / multiple choice, and closer to 1 for
    /// creative and generative tasks.
    /// </remarks>
    [JsonPropertyName("temperature")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? Temperature
    {
        get => this._temperature;
        set
        {
            if (value is < 0.0 or > 1.0) throw new ArgumentOutOfRangeException(nameof(value), value, "Temperature must be between 0.0 and 1.0.");
            this._temperature = value;

            if (this._temperature == null)
            {
                this._topP ??= 0.7;
            }
            else
            {
                this._topP = null;
            }
        }
    }

    /// <summary>
    /// Use nucleus sampling.
    /// </summary>
    /// <remarks>
    /// In nucleus sampling, we compute the cumulative distribution over all the options for each subsequent token in
    /// decreasing probability order and cut it off once it reaches a particular probability specified by top_p. You
    /// should either alter temperature or top_p, but not both.
    /// </remarks>
    [JsonPropertyName("top_p")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? TopP
    {
        get => this._topP;
        set
        {
            this._topP = value;
            if (value == null)
            {
                this._temperature ??= 1.0;
            }
            else
            {
                this._temperature = null;
            }
        }
    }

    /// <summary>
    ///  Only sample from the top K options for each subsequent token.
    /// </summary>
    /// <remarks>
    /// Used to remove "long tail" low probability responses.
    /// </remarks>
    [JsonPropertyName("top_k")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TopK
    {
        get => this._topK;
        set
        {
            if (value is < 1) throw new ArgumentOutOfRangeException(nameof(value), value, "TopK must be greater than zero.");
            this._topK = value;
        }
    }

    /// <summary>
    /// An object describing metadata about the request.
    /// </summary>
    [JsonPropertyName("metadata")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public AnthropicRequestMetadata? Metadata { get; set; }
}
