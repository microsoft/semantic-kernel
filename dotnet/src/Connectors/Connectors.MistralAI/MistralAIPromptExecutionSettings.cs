// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Mistral Execution Settings.
/// </summary>
public sealed class MistralAIPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Default: 0.7
    /// What sampling temperature to use, between 0.0 and 1.0. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    /// </summary>
    /// <remarks>
    /// We generally recommend altering this or top_p but not both.
    /// </remarks>
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
    /// Default: 1
    /// Nucleus sampling, where the model considers the results of the tokens with top_p probability mass.So 0.1 means only the tokens comprising the top 10% probability mass are considered.
    /// </summary>
    /// <remarks>
    /// We generally recommend altering this or temperature but not both.
    /// </remarks>
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
    /// Default: null
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    /// <remarks>
    /// The token count of your prompt plus max_tokens cannot exceed the model's context length.
    /// </remarks>
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
    /// Default: false
    /// Whether to inject a safety prompt before all conversations.
    /// </summary>
    [JsonPropertyName("safe_prompt")]
    public bool SafePrompt
    {
        get => this._safePrompt;

        set
        {
            this.ThrowIfFrozen();
            this._safePrompt = value;
        }
    }

    /// <summary>
    /// Default: null
    /// The seed to use for random sampling. If set, different calls will generate deterministic results.
    /// </summary>
    [JsonPropertyName("random_seed")]
    public int? RandomSeed
    {
        get => this._randomSeed;

        set
        {
            this.ThrowIfFrozen();
            this._randomSeed = value;
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
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new MistralAIPromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this.Temperature,
            TopP = this.TopP,
            MaxTokens = this.MaxTokens,
            SafePrompt = this.SafePrompt,
            RandomSeed = this.RandomSeed,
        };
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <returns>An instance of MistralAIPromptExecutionSettings</returns>
    public static MistralAIPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new MistralAIPromptExecutionSettings()
            {
            };
        }

        if (executionSettings is MistralAIPromptExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var mistralExecutionSettings = JsonSerializer.Deserialize<MistralAIPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (mistralExecutionSettings is not null)
        {
            return mistralExecutionSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(MistralAIPromptExecutionSettings)}", nameof(executionSettings));
    }

    #region private ================================================================================

    private double _temperature = 0.7;
    private double _topP = 1;
    private int? _maxTokens;
    private bool _safePrompt = false;
    private int? _randomSeed;

    #endregion
}
