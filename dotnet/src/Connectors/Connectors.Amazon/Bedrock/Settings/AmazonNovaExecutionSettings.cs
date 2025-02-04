// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Prompt execution settings for Nova Text Generation
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public class AmazonNovaExecutionSettings : PromptExecutionSettings
{
    private string? _schemaVersion;
    private int? _maxNewTokens;
    private float? _topP;
    private int? _topK;
    private float? _temperature;
    private List<string>? _stopSequences;

    /// <summary>
    /// Schema version for the execution settings.
    /// </summary>
    [JsonPropertyName("schemaVersion")]
    public string? SchemaVersion
    {
        get => this._schemaVersion;
        set
        {
            this.ThrowIfFrozen();
            this._schemaVersion = value;
        }
    }

    /// <summary>
    /// Maximum new tokens to generate in the response.
    /// </summary>
    [JsonPropertyName("max_new_tokens")]
    public int? MaxNewTokens
    {
        get => this._maxNewTokens;
        set
        {
            this.ThrowIfFrozen();
            this._maxNewTokens = value;
        }
    }

    /// <summary>
    /// Top P controls token choices, based on the probability of the potential choices. The range is 0 to 1. The default is 1.
    /// </summary>
    [JsonPropertyName("top_p")]
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
    /// Top K limits the number of token options considered at each generation step. The default is 20.
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
    /// Converts PromptExecutionSettings to NovaExecutionSettings
    /// </summary>
    /// <param name="executionSettings">The Kernel standard PromptExecutionSettings.</param>
    /// <returns>Model specific execution settings</returns>
    public static AmazonNovaExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AmazonNovaExecutionSettings();
            case AmazonNovaExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<AmazonNovaExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}
