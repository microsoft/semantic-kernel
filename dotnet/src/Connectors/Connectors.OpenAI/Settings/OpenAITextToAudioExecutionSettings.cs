// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Execution settings for OpenAI text-to-audio request.
/// </summary>
[Experimental("SKEXP0001")]
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class OpenAITextToAudioExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// The voice to use when generating the audio. Supported voices are alloy, echo, fable, onyx, nova, and shimmer.
    /// </summary>
    [JsonPropertyName("voice")]
    public string Voice
    {
        get => this._voice;

        set
        {
            this.ThrowIfFrozen();
            this._voice = value;
        }
    }

    /// <summary>
    /// The format to audio in. Supported formats are mp3, opus, aac, and flac.
    /// </summary>
    [JsonPropertyName("response_format")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ResponseFormat
    {
        get => this._responseFormat;

        set
        {
            this.ThrowIfFrozen();
            this._responseFormat = value;
        }
    }

    /// <summary>
    /// The speed of the generated audio. Select a value from 0.25 to 4.0. 1.0 is the default.
    /// </summary>
    [JsonPropertyName("speed")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? Speed
    {
        get => this._speed;

        set
        {
            this.ThrowIfFrozen();
            this._speed = value;
        }
    }

    /// <summary>
    /// Creates an instance of <see cref="OpenAITextToAudioExecutionSettings"/> class with default voice - "alloy".
    /// </summary>
    public OpenAITextToAudioExecutionSettings()
        : this(DefaultVoice)
    {
    }

    /// <summary>
    /// Creates an instance of <see cref="OpenAITextToAudioExecutionSettings"/> class.
    /// </summary>
    /// <param name="voice">The voice to use when generating the audio. Supported voices are alloy, echo, fable, onyx, nova, and shimmer.</param>
    public OpenAITextToAudioExecutionSettings(string? voice)
    {
        this._voice = voice ?? DefaultVoice;
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new OpenAITextToAudioExecutionSettings(this.Voice)
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Speed = this.Speed,
            ResponseFormat = this.ResponseFormat
        };
    }

    /// <summary>
    /// Converts <see cref="PromptExecutionSettings"/> to derived <see cref="OpenAITextToAudioExecutionSettings"/> type.
    /// </summary>
    /// <param name="executionSettings">Instance of <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>Instance of <see cref="OpenAITextToAudioExecutionSettings"/>.</returns>
    public static OpenAITextToAudioExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new OpenAITextToAudioExecutionSettings();
        }

        if (executionSettings is OpenAITextToAudioExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAITextToAudioExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        return openAIExecutionSettings!;
    }

    #region private ================================================================================

    private const string DefaultVoice = "alloy";

    private float? _speed;
    private string? _responseFormat;
    private string _voice;

    #endregion
}
