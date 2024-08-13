// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Prompt execution settings for Amazon Titan Text Generation
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public class AmazonTitanExecutionSettings : PromptExecutionSettings
{
    private float? _topP;
    private float? _temperature;
    private int? _maxTokenCount;
    private List<string>? _stopSequences;

    /// <summary>
    /// Top P controls token choices, based on the probability of the potential choices. The range is 0 to 1. The default is 1.
    /// </summary>
    [JsonPropertyName("topP")]
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
    /// The Temperature value ranges from 0 to 1, with 0 being the most deterministic and 1 being the most creative.
    /// </summary>
    [JsonPropertyName("temperature")]
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
    /// Configures the maximum number of tokens in the generated response. The range is 0 to 4096. The default is 512.
    /// </summary>
    [JsonPropertyName("maxTokenCount")]
    public int? MaxTokenCount
    {
        get => this._maxTokenCount;
        set
        {
            this.ThrowIfFrozen();
            this._maxTokenCount = value;
        }
    }

    /// <summary>
    /// Use | (pipe) characters (maximum 20 characters).
    /// </summary>
    [JsonPropertyName("stopSequences")]
    public List<string>? StopSequences
    {
        get => this._stopSequences;
        set
        {
            this.ThrowIfFrozen();
            this._stopSequences = value;
        }
    }

    /// <summary>
    /// Converts PromptExecutionSettings to AmazonTitanExecutionSettings
    /// </summary>
    /// <param name="executionSettings">The Kernel standard PromptExecutionSettings.</param>
    /// <returns>Model specific execution settings</returns>
    public static AmazonTitanExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AmazonTitanExecutionSettings();
            case AmazonTitanExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<AmazonTitanExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}
