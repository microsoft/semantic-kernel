// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Text.Json;
using System.Text.Json.Serialization;
using Azure.AI.Inference;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AzureAIInference;

/// <summary>
/// Chat completion prompt execution settings.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class AzureAIInferencePromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIInferencePromptExecutionSettings"/> class.
    /// </summary>
    public AzureAIInferencePromptExecutionSettings()
    {
        this.ExtensionData = new Dictionary<string, object>();
    }

    /// <summary>
    /// Allowed values: "error" | "drop" | "pass-through"
    /// </summary>
    [JsonPropertyName("extra_parameters")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ExtraParameters
    {
        get => this._extraParameters;
        set
        {
            this.ThrowIfFrozen();
            this._extraParameters = value;
        }
    }

    /// <summary>
    /// A value that influences the probability of generated tokens appearing based on their cumulative
    /// frequency in generated text.
    /// Positive values will make tokens less likely to appear as their frequency increases and
    /// decrease the likelihood of the model repeating the same statements verbatim.
    /// Supported range is [-2, 2].
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? FrequencyPenalty
    {
        get => this._frequencyPenalty;
        set
        {
            this.ThrowIfFrozen();
            this._frequencyPenalty = value;
        }
    }

    /// <summary>
    /// A value that influences the probability of generated tokens appearing based on their existing
    /// presence in generated text.
    /// Positive values will make tokens less likely to appear when they already exist and increase the
    /// model's likelihood to output new topics.
    /// Supported range is [-2, 2].
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? PresencePenalty
    {
        get => this._presencePenalty;
        set
        {
            this.ThrowIfFrozen();
            this._presencePenalty = value;
        }
    }

    /// <summary>
    /// The sampling temperature to use that controls the apparent creativity of generated completions.
    /// Higher values will make output more random while lower values will make results more focused
    /// and deterministic.
    /// It is not recommended to modify temperature and top_p for the same completions request as the
    /// interaction of these two settings is difficult to predict.
    /// Supported range is [0, 1].
    /// </summary>
    [JsonPropertyName("temperature")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
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
    /// An alternative to sampling with temperature called nucleus sampling. This value causes the
    /// model to consider the results of tokens with the provided probability mass. As an example, a
    /// value of 0.15 will cause only the tokens comprising the top 15% of probability mass to be
    /// considered.
    /// It is not recommended to modify temperature and top_p for the same completions request as the
    /// interaction of these two settings is difficult to predict.
    /// Supported range is [0, 1].
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? NucleusSamplingFactor
    {
        get => this._nucleusSamplingFactor;
        set
        {
            this.ThrowIfFrozen();
            this._nucleusSamplingFactor = value;
        }
    }

    /// <summary> The maximum number of tokens to generate. </summary>
    [JsonPropertyName("max_tokens")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
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
    /// The format that the model must output. Use this to enable JSON mode instead of the default text mode.
    /// Note that to enable JSON mode, some AI models may also require you to instruct the model to produce JSON
    /// via a system or user message.
    /// Please note <see cref="ChatCompletionsResponseFormat"/> is the base class. According to the scenario, a derived class of the base class might need to be assigned here, or this property needs to be casted to one of the possible derived classes.
    /// The available derived classes include <see cref="ChatCompletionsResponseFormatJsonObject"/> and <see cref="ChatCompletionsResponseFormatText"/>.
    /// </summary>
    [JsonPropertyName("response_format")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? ResponseFormat
    {
        get => this._responseFormat;
        set
        {
            this.ThrowIfFrozen();
            this._responseFormat = value;
        }
    }

    /// <summary> A collection of textual sequences that will end completions generation. </summary>
    [JsonPropertyName("stop")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
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
    /// The available tool definitions that the chat completions request can use, including caller-defined functions.
    /// Please note <see cref="ChatCompletionsToolDefinition"/> is the base class. According to the scenario, a derived class of the base class might need to be assigned here, or this property needs to be casted to one of the possible derived classes.
    /// The available derived classes include <see cref="ChatCompletionsToolDefinition"/>.
    /// </summary>
    [JsonPropertyName("tools")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<ChatCompletionsToolDefinition>? Tools
    {
        get => this._tools;
        set
        {
            this.ThrowIfFrozen();
            this._tools = value;
        }
    }

    /// <summary>
    /// If specified, the system will make a best effort to sample deterministically such that repeated requests with the
    /// same seed and parameters should return the same result. Determinism is not guaranteed.
    /// </summary>
    [JsonPropertyName("seed")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public long? Seed
    {
        get => this._seed;
        set
        {
            this.ThrowIfFrozen();
            this._seed = value;
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

        if (this._tools is not null)
        {
            this._tools = new ReadOnlyCollection<ChatCompletionsToolDefinition>(this._tools);
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new AzureAIInferencePromptExecutionSettings()
        {
            ExtraParameters = this.ExtraParameters,
            FrequencyPenalty = this.FrequencyPenalty,
            PresencePenalty = this.PresencePenalty,
            Temperature = this.Temperature,
            NucleusSamplingFactor = this.NucleusSamplingFactor,
            MaxTokens = this.MaxTokens,
            ResponseFormat = this.ResponseFormat,
            StopSequences = this.StopSequences is not null ? new List<string>(this.StopSequences) : null,
            Tools = this.Tools is not null ? new List<ChatCompletionsToolDefinition>(this.Tools) : null,
            Seed = this.Seed,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
        };
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <returns>An instance of <see cref="AzureAIInferencePromptExecutionSettings"/></returns>
    public static AzureAIInferencePromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new AzureAIInferencePromptExecutionSettings();
        }

        if (executionSettings is AzureAIInferencePromptExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var aiInferenceSettings = JsonSerializer.Deserialize<AzureAIInferencePromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (aiInferenceSettings is not null)
        {
            return aiInferenceSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(AzureAIInferencePromptExecutionSettings)}", nameof(executionSettings));
    }

    #region private ================================================================================

    private string? _extraParameters;
    private float? _frequencyPenalty;
    private float? _presencePenalty;
    private float? _temperature;
    private float? _nucleusSamplingFactor;
    private int? _maxTokens;
    private object? _responseFormat;
    private IList<string>? _stopSequences;
    private IList<ChatCompletionsToolDefinition>? _tools;
    private long? _seed;

    #endregion
}
