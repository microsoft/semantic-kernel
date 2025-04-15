// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Execution settings for OpenAI audio-to-text request.
/// </summary>
[Experimental("SKEXP0010")]
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class OpenAIAudioToTextExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Filename or identifier associated with audio data.
    /// Should be in format {filename}.{extension}
    /// </summary>
    [JsonPropertyName("filename")]
    public string Filename
    {
        get => this._filename;

        set
        {
            this.ThrowIfFrozen();
            this._filename = value;
        }
    }

    /// <summary>
    /// An optional language of the audio data as two-letter ISO-639-1 language code (e.g. 'en' or 'es').
    /// </summary>
    [JsonPropertyName("language")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Language
    {
        get => this._language;

        set
        {
            this.ThrowIfFrozen();
            this._language = value;
        }
    }

    /// <summary>
    /// An optional text to guide the model's style or continue a previous audio segment. The prompt should match the audio language.
    /// </summary>
    [JsonPropertyName("prompt")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Prompt
    {
        get => this._prompt;

        set
        {
            this.ThrowIfFrozen();
            this._prompt = value;
        }
    }

    /// <summary>
    /// The format of the transcript output, in one of these options: json, srt, verbose_json, or vtt. Default is 'json'.
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
    /// The sampling temperature, between 0 and 1.
    /// Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    /// If set to 0, the model will use log probability to automatically increase the temperature until certain thresholds are hit.
    /// Default is 0.
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
    /// The timestamp granularities to populate for this transcription. response_format must be set <c>verbose_json</c> to use timestamp granularities.
    /// Either or both of these options are supported: word, or segment.
    /// </summary>
    /// <remarks>
    /// There is no additional latency for segment timestamps, but generating word timestamps incurs additional latency.
    /// </remarks>
    [JsonPropertyName("timestamp_granularities")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<string>? TimestampGranularities
    {
        get => this._timestampGranularities;

        set
        {
            this.ThrowIfFrozen();
            this._timestampGranularities = value;
        }
    }

    /// <summary>
    /// Creates an instance of <see cref="OpenAIAudioToTextExecutionSettings"/> class with default filename - "file.mp3".
    /// </summary>
    public OpenAIAudioToTextExecutionSettings()
        : this(DefaultFilename)
    {
    }

    /// <summary>
    /// Creates an instance of <see cref="OpenAIAudioToTextExecutionSettings"/> class.
    /// </summary>
    /// <param name="filename">Filename or identifier associated with audio data. Should be in format {filename}.{extension}</param>
    public OpenAIAudioToTextExecutionSettings(string filename)
    {
        this._filename = filename;
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new OpenAIAudioToTextExecutionSettings(this.Filename)
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this.Temperature,
            ResponseFormat = this.ResponseFormat,
            Language = this.Language,
            Prompt = this.Prompt
        };
    }

    /// <summary>
    /// Converts <see cref="PromptExecutionSettings"/> to derived <see cref="OpenAIAudioToTextExecutionSettings"/> type.
    /// </summary>
    /// <param name="executionSettings">Instance of <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>Instance of <see cref="OpenAIAudioToTextExecutionSettings"/>.</returns>
    public static OpenAIAudioToTextExecutionSettings? FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new OpenAIAudioToTextExecutionSettings();
        }

        if (executionSettings is OpenAIAudioToTextExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAIAudioToTextExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        return openAIExecutionSettings!;
    }

    #region private ================================================================================

    private const string DefaultFilename = "file.mp3";

    private float? _temperature = 0;
    private string? _responseFormat;
    private string _filename;
    private string? _language;
    private string? _prompt;
    private IList<string>? _timestampGranularities;

    #endregion
}
