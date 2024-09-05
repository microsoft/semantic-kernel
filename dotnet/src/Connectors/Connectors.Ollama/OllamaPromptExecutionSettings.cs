// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;
using OllamaSharp.Models;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Ollama Chat Completion and Text Generation Execution Settings.
/// </summary>
public sealed class OllamaPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaPromptExecutionSettings"/> class.
    /// </summary>
    /// <param name="requestOptions">Optional breaking glass request options</param>
    public OllamaPromptExecutionSettings(RequestOptions? requestOptions = null)
    {
        this._requestOptions = requestOptions ?? new();
    }

    /// <summary>
    /// Gets the specialization for the Ollama execution settings.
    /// </summary>
    /// <param name="executionSettings">Generic prompt execution settings.</param>
    /// <returns>Specialized Ollama execution settings.</returns>
    public static OllamaPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new();
            case OllamaPromptExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        var ollamaExecutionSettings = JsonSerializer.Deserialize<OllamaPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (ollamaExecutionSettings is not null)
        {
            return ollamaExecutionSettings;
        }

        throw new ArgumentException(
            $"Invalid execution settings, cannot convert to {nameof(OllamaPromptExecutionSettings)}",
            nameof(executionSettings));
    }

    /// <summary>
    /// Sets the stop sequences to use. When this pattern is encountered the
    /// LLM will stop generating text and return. Multiple stop patterns may
    /// be set by specifying multiple separate stop parameters in a model file.
    /// </summary>
    [JsonPropertyName("stop")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<string>? Stop
    {
        get => this._requestOptions.Stop;

        set
        {
            this.ThrowIfFrozen();
            this._requestOptions.Stop = value?.ToArray();
        }
    }

    /// <summary>
    /// Reduces the probability of generating nonsense. A higher value
    /// (e.g. 100) will give more diverse answers, while a lower value (e.g. 10)
    /// will be more conservative. (Default: 40)
    /// </summary>
    [JsonPropertyName("top_k")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TopK
    {
        get => this._requestOptions.TopK;

        set
        {
            this.ThrowIfFrozen();
            this._requestOptions.TopK = value;
        }
    }

    /// <summary>
    /// Works together with top-k. A higher value (e.g., 0.95) will lead to
    /// more diverse text, while a lower value (e.g., 0.5) will generate more
    /// focused and conservative text. (Default: 0.9)
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? TopP
    {
        get => this._requestOptions.TopP;

        set
        {
            this.ThrowIfFrozen();
            this._requestOptions.TopP = value;
        }
    }

    /// <summary>
    /// The temperature of the model. Increasing the temperature will make the
    /// model answer more creatively. (Default: 0.8)
    /// </summary>
    [JsonPropertyName("temperature")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? Temperature
    {
        get => this._requestOptions.Temperature;

        set
        {
            this.ThrowIfFrozen();
            this._requestOptions.Temperature = value;
        }
    }

    /// <summary>
    /// The breaking glass request options.
    /// </summary>
    internal RequestOptions RequestOptions => this._requestOptions;

    #region private

    private readonly RequestOptions _requestOptions;

    #endregion
}
