// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Prompt execution settings for Meta Llama 3 Text Generation
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public class AmazonLlama3ExecutionSettings : PromptExecutionSettings
{
    private float? _temperature;
    private float? _topP;
    private int? _maxGenLen;

    /// <summary>
    /// Use a lower value to decrease randomness in the response.
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
    /// Use a lower value to ignore less probable options. Set to 0 or 1.0 to disable.
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
    /// Specify the maximum number of tokens to use in the generated response. The model truncates the response once the generated text exceeds max_gen_len.
    /// </summary>
    [JsonPropertyName("max_gen_len")]
    public int? MaxGenLen
    {
        get => this._maxGenLen;
        set
        {
            this.ThrowIfFrozen();
            this._maxGenLen = value;
        }
    }

    /// <summary>
    /// Converts PromptExecutionSettings to AmazonLlama3ExecutionSettings
    /// </summary>
    /// <param name="executionSettings">The Kernel standard PromptExecutionSettings.</param>
    /// <returns>Model specific execution settings</returns>
    public static AmazonLlama3ExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AmazonLlama3ExecutionSettings();
            case AmazonLlama3ExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<AmazonLlama3ExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}
