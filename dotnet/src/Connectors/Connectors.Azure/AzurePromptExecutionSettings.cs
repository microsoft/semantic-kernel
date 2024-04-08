// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Azure;

/// <summary>
/// Execution settings for an Azure completion request.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class AzurePromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// Default is 1.0.
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
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// Default is 1.0.
    /// </summary>
    [JsonPropertyName("top_p")]
    public double TopP
    {
        get => this._topP;

        set
        {
            this.ThrowIfFrozen();
            this._topP = value;
        }
    }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    public double PresencePenalty
    {
        get => this._presencePenalty;

        set
        {
            this.ThrowIfFrozen();
            this._presencePenalty = value;
        }
    }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    public double FrequencyPenalty
    {
        get => this._frequencyPenalty;

        set
        {
            this.ThrowIfFrozen();
            this._frequencyPenalty = value;
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
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    public IList<string>? StopSequences
    {
        get => this._stopSequences;

        set
        {
            this.ThrowIfFrozen();
            this._stopSequences = value;
        }
    }

    /// <summary>
    /// How many completions to generate for each prompt. Default is 1.
    /// Note: Because this parameter generates many completions, it can quickly consume your token quota.
    /// Use carefully and ensure that you have reasonable settings for max_tokens and stop.
    /// </summary>
    [JsonPropertyName("results_per_prompt")]
    public int ResultsPerPrompt
    {
        get => this._resultsPerPrompt;

        set
        {
            this.ThrowIfFrozen();
            this._resultsPerPrompt = value;
        }
    }

    /// <summary>
    /// If specified, the system will make a best effort to sample deterministically such that repeated requests with the
    /// same seed and parameters should return the same result. Determinism is not guaranteed.
    /// </summary>
    [JsonPropertyName("seed")]
    public long? Seed
    {
        get => this._seed;

        set
        {
            this.ThrowIfFrozen();
            this._seed = value;
        }
    }

    /// <summary>
    /// The system prompt to use when generating text using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    [JsonPropertyName("chat_system_prompt")]
    public string? ChatSystemPrompt
    {
        get => this._chatSystemPrompt;

        set
        {
            this.ThrowIfFrozen();
            this._chatSystemPrompt = value;
        }
    }

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    [JsonPropertyName("token_selection_biases")]
    public IDictionary<int, int>? TokenSelectionBiases
    {
        get => this._tokenSelectionBiases;

        set
        {
            this.ThrowIfFrozen();
            this._tokenSelectionBiases = value;
        }
    }

    /// <inheritdoc/>
    public override void Freeze()
    {
        if (this.IsFrozen)
        {
            return;
        }

        base.Freeze();

        if (this._stopSequences is not null)
        {
            this._stopSequences = new ReadOnlyCollection<string>(this._stopSequences);
        }

        if (this._tokenSelectionBiases is not null)
        {
            this._tokenSelectionBiases = new ReadOnlyDictionary<int, int>(this._tokenSelectionBiases);
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new AzurePromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this.Temperature,
            TopP = this.TopP,
            PresencePenalty = this.PresencePenalty,
            FrequencyPenalty = this.FrequencyPenalty,
            MaxTokens = this.MaxTokens,
            StopSequences = this.StopSequences is not null ? new List<string>(this.StopSequences) : null,
            ResultsPerPrompt = this.ResultsPerPrompt,
            Seed = this.Seed,
            TokenSelectionBiases = this.TokenSelectionBiases is not null ? new Dictionary<int, int>(this.TokenSelectionBiases) : null,
            ChatSystemPrompt = this.ChatSystemPrompt
        };
    }

    /// <summary>
    /// Default max tokens for a text generation
    /// </summary>
    internal static int DefaultTextMaxTokens { get; } = 256;

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <param name="defaultMaxTokens">Default max tokens</param>
    /// <returns>An instance of OpenAIPromptExecutionSettings</returns>
    public static AzurePromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
    {
        if (executionSettings is null)
        {
            return new AzurePromptExecutionSettings()
            {
                MaxTokens = defaultMaxTokens
            };
        }

        if (executionSettings is AzurePromptExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<AzurePromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (openAIExecutionSettings is not null)
        {
            return openAIExecutionSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(AzurePromptExecutionSettings)}", nameof(executionSettings));
    }

    #region private ================================================================================

    private double _temperature = 1;
    private double _topP = 1;
    private double _presencePenalty;
    private double _frequencyPenalty;
    private int? _maxTokens;
    private IList<string>? _stopSequences;
    private int _resultsPerPrompt = 1;
    private long? _seed;
    private IDictionary<int, int>? _tokenSelectionBiases;
    private string? _chatSystemPrompt;

    #endregion
}
