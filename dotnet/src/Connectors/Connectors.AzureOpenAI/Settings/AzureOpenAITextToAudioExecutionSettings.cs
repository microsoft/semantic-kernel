// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Execution settings for Azure OpenAI text-to-audio request.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class AzureOpenAITextToAudioExecutionSettings : PromptExecutionSettings
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
    public string ResponseFormat
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
    public float Speed
    {
        get => this._speed;

        set
        {
            this.ThrowIfFrozen();
            this._speed = value;
        }
    }

    /// <summary>
    /// Creates an instance of <see cref="AzureOpenAITextToAudioExecutionSettings"/> class with default voice - "alloy".
    /// </summary>
    public AzureOpenAITextToAudioExecutionSettings()
        : this(DefaultVoice)
    {
    }

    /// <summary>
    /// Creates an instance of <see cref="AzureOpenAITextToAudioExecutionSettings"/> class.
    /// </summary>
    /// <param name="voice">The voice to use when generating the audio. Supported voices are alloy, echo, fable, onyx, nova, and shimmer.</param>
    public AzureOpenAITextToAudioExecutionSettings(string voice)
    {
        this._voice = voice;
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new AzureOpenAITextToAudioExecutionSettings(this.Voice)
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Speed = this.Speed,
            ResponseFormat = this.ResponseFormat
        };
    }

    /// <summary>
    /// Converts <see cref="PromptExecutionSettings"/> to derived <see cref="AzureOpenAITextToAudioExecutionSettings"/> type.
    /// </summary>
    /// <param name="executionSettings">Instance of <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>Instance of <see cref="AzureOpenAITextToAudioExecutionSettings"/>.</returns>
    public static AzureOpenAITextToAudioExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new AzureOpenAITextToAudioExecutionSettings();
        }

        if (executionSettings is AzureOpenAITextToAudioExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var azureOpenAIExecutionSettings = JsonSerializer.Deserialize<AzureOpenAITextToAudioExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        if (azureOpenAIExecutionSettings is not null)
        {
            return azureOpenAIExecutionSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(AzureOpenAITextToAudioExecutionSettings)}", nameof(executionSettings));
    }

    #region private ================================================================================

    private const string DefaultVoice = "alloy";

    private float _speed = 1.0f;
    private string _responseFormat = "mp3";
    private string _voice;

    #endregion
}
