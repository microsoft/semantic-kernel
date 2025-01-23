// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Ollama Prompt Execution Settings.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class OllamaPromptExecutionSettings : PromptExecutionSettings
{
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
        if (ollamaExecutionSettings is null)
        {
            throw new ArgumentException(
            $"Invalid execution settings, cannot convert to {nameof(OllamaPromptExecutionSettings)}",
            nameof(executionSettings));
        }

        // Restore the function choice behavior that lost internal state(list of function instances) during serialization/deserialization process.
        ollamaExecutionSettings!.FunctionChoiceBehavior = executionSettings.FunctionChoiceBehavior;

        return ollamaExecutionSettings;
    }

    /// <summary>
    /// Sets the stop sequences to use. When this pattern is encountered the
    /// LLM will stop generating text and return. Multiple stop patterns may
    /// be set by specifying multiple separate stop parameters in a model file.
    /// </summary>
    [JsonPropertyName("stop")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string>? Stop
    {
        get => this._stop;

        set
        {
            this.ThrowIfFrozen();
            this._stop = value;
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
        get => this._topK;

        set
        {
            this.ThrowIfFrozen();
            this._topK = value;
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
        get => this._topP;

        set
        {
            this.ThrowIfFrozen();
            this._topP = value;
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
        get => this._temperature;

        set
        {
            this.ThrowIfFrozen();
            this._temperature = value;
        }
    }

    /// <summary>
    /// Maximum number of output tokens. (Default: -1, infinite generation)
    /// </summary>
    [JsonPropertyName("num_predict")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? NumPredict
    {
        get => this._numPredict;

        set
        {
            this.ThrowIfFrozen();
            this._numPredict = value;
        }
    }

    #region private

    private List<string>? _stop;
    private float? _temperature;
    private float? _topP;
    private int? _topK;
    private int? _numPredict;

    #endregion
}
