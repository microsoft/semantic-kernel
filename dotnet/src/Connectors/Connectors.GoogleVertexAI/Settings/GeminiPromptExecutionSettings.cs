// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents the settings for executing a prompt with the Gemini model.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class GeminiPromptExecutionSettings : PromptExecutionSettings
{
    private double? _temperature;
    private double? _topP;
    private int? _topK;
    private int? _maxTokens;
    private int? _candidateCount;
    private IList<string>? _stopSequences;
    private IList<GeminiSafetySetting>? _safetySettings;

    /// <summary>
    /// Default max tokens for a text generation.
    /// </summary>
    public static int DefaultTextMaxTokens { get; } = 256;

    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// Range is 0.0 to 1.0.
    /// </summary>
    [JsonPropertyName("temperature")]
    public double? Temperature
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
    /// Gets or sets the value of the TopK property.
    /// The TopK property represents the maximum value of a collection or dataset.
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
    /// The count of candidates. Possible values range from 1 to 8.
    /// </summary>
    [JsonPropertyName("candidate_count")]
    public int? CandidateCount
    {
        get => this._candidateCount;
        set
        {
            this.ThrowIfFrozen();
            this._candidateCount = value;
        }
    }

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// Maximum number of stop sequences is 5.
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
    /// Represents a list of safety settings.
    /// </summary>
    [JsonPropertyName("safety_settings")]
    public IList<GeminiSafetySetting>? SafetySettings
    {
        get => this._safetySettings;
        set
        {
            this.ThrowIfFrozen();
            this._safetySettings = value;
        }
    }

    /// <inheritdoc />
    public override void Freeze()
    {
        base.Freeze();

        if (this._stopSequences is not null)
        {
            this._stopSequences = new ReadOnlyCollection<string>(this._stopSequences);
        }

        if (this._safetySettings is not null)
        {
            this._safetySettings = new ReadOnlyCollection<GeminiSafetySetting>(this._safetySettings);
        }
    }

    /// <inheritdoc />
    public override PromptExecutionSettings Clone()
    {
        return new GeminiPromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this.Temperature,
            TopP = this.TopP,
            TopK = this.TopK,
            MaxTokens = this.MaxTokens,
            CandidateCount = this.CandidateCount,
            StopSequences = this.StopSequences?.ToList(),
            SafetySettings = this.SafetySettings?.Select(setting => new GeminiSafetySetting(setting)).ToList(),
        };
    }

    /// <summary>
    /// Converts a <see cref="PromptExecutionSettings"/> object to a <see cref="GeminiPromptExecutionSettings"/> object.
    /// </summary>
    /// <param name="executionSettings">The <see cref="PromptExecutionSettings"/> object to convert.</param>
    /// <returns>
    /// The converted <see cref="GeminiPromptExecutionSettings"/> object. If <paramref name="executionSettings"/> is null,
    /// a new instance of <see cref="GeminiPromptExecutionSettings"/> is returned. If <paramref name="executionSettings"/>
    /// is already a <see cref="GeminiPromptExecutionSettings"/> object, it is casted and returned. Otherwise, the method
    /// tries to deserialize <paramref name="executionSettings"/> to a <see cref="GeminiPromptExecutionSettings"/> object.
    /// If deserialization is successful, the converted object is returned. If deserialization fails or the converted object
    /// is null, an <see cref="ArgumentException"/> is thrown.
    /// </returns>
    public static GeminiPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new GeminiPromptExecutionSettings() { MaxTokens = DefaultTextMaxTokens };
            case GeminiPromptExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        var geminiExecutionSettings = JsonSerializer.Deserialize<GeminiPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (geminiExecutionSettings is not null)
        {
            return geminiExecutionSettings;
        }

        throw new ArgumentException(
            $"Invalid execution settings, cannot convert to {nameof(GeminiPromptExecutionSettings)}",
            nameof(executionSettings));
    }
}
