// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

/// <summary>
/// Ollama Execution Settings.
/// </summary>
public sealed class HuggingFacePromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Default max tokens for a text generation.
    /// </summary>
    public static int DefaultTextMaxTokens { get; } = 256;

    /// <summary>
    /// Gets the specialization for the Ollama execution settings.
    /// </summary>
    /// <param name="executionSettings">Generic prompt execution settings.</param>
    /// <returns>Specialized Ollama execution settings.</returns>
    public static HuggingFacePromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new HuggingFacePromptExecutionSettings() { MaxTokens = DefaultTextMaxTokens };
            case HuggingFacePromptExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        var ollamaExecutionSettings = JsonSerializer.Deserialize<HuggingFacePromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (ollamaExecutionSettings is not null)
        {
            return ollamaExecutionSettings;
        }

        throw new ArgumentException(
            $"Invalid execution settings, cannot convert to {nameof(HuggingFacePromptExecutionSettings)}",
            nameof(executionSettings));
    }

    /// <summary>
    /// (Default: 1.0). Float (0.0-100.0). The temperature of the sampling operation. 1 means regular sampling,
    /// 0 means always take the highest score, 100.0 is getting closer to uniform probability.
    /// </summary>
    [JsonPropertyName("temperature")]
    public double Temperature
    {
        get => this._temperature;

        set
        {
            this.ThrowIfFrozen();
            this._temperature = value;
        }
    }

    /// <summary>
    /// (Default: None). Integer to define the top tokens considered within the sample operation to create new text.
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
    /// The maximum number of tokens to generate in the completion.
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
    /// (Default: None). Float (0-120.0). The amount of time in seconds that the query should take maximum.
    /// Network can cause some overhead so it will be a soft limit. Use that in combination with max_new_tokens for best results.
    /// </summary>
    [JsonPropertyName("max_time")]
    public double? MaxTime
    {
        get => this._maxTime;

        set
        {
            this.ThrowIfFrozen();
            this._maxTime = value;
        }
    }

    /// <summary>
    /// (Default: None). Float to define the tokens that are within the sample operation of text generation.
    /// Add tokens in the sample for more probable to least probable until the sum of the probabilities is greater than top_p.
    /// </summary>
    [JsonPropertyName("top_p")]
    public double? TopP
    {
        get => this._topP;

        set
        {
            this.ThrowIfFrozen();
            this._topP = value;
        }
    }

    /// <summary>
    /// (Default: None). Float (0.0-100.0). The more a token is used within generation the more
    /// it is penalized to not be picked in successive generation passes.
    /// </summary>
    [JsonPropertyName("repetition_penalty")]
    public double RepetitionPenalty
    {
        get => this._repetitionPenalty;

        set
        {
            this.ThrowIfFrozen();
            this._repetitionPenalty = value;
        }
    }

    /// <summary>
    /// (Default: true). Boolean. There is a cache layer on the inference API to speedup requests we have already seen.
    /// Most models can use those results as is as models are deterministic (meaning the results will be the same anyway).
    /// However if you use a non deterministic model, you can set this parameter to prevent the caching mechanism from being used
    /// resulting in a real new query.
    /// </summary>
    [JsonPropertyName("use_cache")]
    public bool UseCache
    {
        get => this._useCache;

        set
        {
            this.ThrowIfFrozen();
            this._useCache = value;
        }
    }

    /// <summary>
    /// (Default: false) Boolean. If the model is not ready, wait for it instead of receiving 503.
    /// It limits the number of requests required to get your inference done.
    /// It is advised to only set this flag to true after receiving a 503 error as it will limit hanging in your application to known places.
    /// </summary>
    [JsonPropertyName("wait_for_model")]
    public bool WaitForModel
    {
        get => this._waitForModel;

        set
        {
            this.ThrowIfFrozen();
            this._waitForModel = value;
        }
    }

    private double _temperature = 1;
    private double? _topP;
    private double _repetitionPenalty;
    private int? _maxTokens;
    private double? _maxTime;
    private int? _topK;
    private bool _useCache = true;
    private bool _waitForModel = false;
}
