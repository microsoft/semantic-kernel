// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Prompt execution settings for Cohere Command Text Generation
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public class AmazonCommandExecutionSettings : PromptExecutionSettings
{
    private double? _temperature;
    private double? _topP;
    private double? _topK;
    private int? _maxTokens;
    private List<string>? _stopSequences;
    private string? _returnLikelihoods;
    private bool? _stream;
    private int? _numGenerations;
    private Dictionary<int, double>? _logitBias;
    private string? _truncate;

    /// <summary>
    /// Use a lower value to decrease randomness in the response.
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
    /// Top P. Use a lower value to ignore less probable options. Set to 0 or 1.0 to disable. If both p and k are enabled, p acts after k.
    /// </summary>
    [JsonPropertyName("p")]
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
    /// Top K. Specify the number of token choices the model uses to generate the next token. If both p and k are enabled, p acts after k.
    /// </summary>
    [JsonPropertyName("k")]
    public double? TopK
    {
        get => this._topK;
        set
        {
            this.ThrowIfFrozen();
            this._topK = value;
        }
    }

    /// <summary>
    /// Specify the maximum number of tokens to use in the generated response.
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
    /// Configure up to four sequences that the model recognizes. After a stop sequence, the model stops generating further tokens. The returned text doesn't contain the stop sequence.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
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
    /// Specify how and if the token likelihoods are returned with the response. You can specify the following options: GENERATION, ALL, or NONE.
    /// </summary>
    [JsonPropertyName("return_likelihoods")]
    public string? ReturnLikelihoods
    {
        get => this._returnLikelihoods;
        set
        {
            this.ThrowIfFrozen();
            this._returnLikelihoods = value;
        }
    }

    /// <summary>
    /// (Required to support streaming) Specify true to return the response piece-by-piece in real-time and false to return the complete response after the process finishes.
    /// </summary>
    [JsonPropertyName("stream")]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? Stream
    {
        get => this._stream;
        set
        {
            this.ThrowIfFrozen();
            this._stream = value;
        }
    }

    /// <summary>
    /// The maximum number of generations that the model should return.
    /// </summary>
    [JsonPropertyName("num_generations")]
    public int? NumGenerations
    {
        get => this._numGenerations;
        set
        {
            this.ThrowIfFrozen();
            this._numGenerations = value;
        }
    }

    /// <summary>
    /// Prevents the model from generating unwanted tokens or incentivizes the model to include desired tokens. The format is {token_id: bias} where bias is a float between -10 and 10. Tokens can be obtained from text using any tokenization service, such as Cohere's Tokenize endpoint.
    /// </summary>
    [JsonPropertyName("logit_bias")]
    public Dictionary<int, double>? LogitBias
    {
        get => this._logitBias;
        set
        {
            this.ThrowIfFrozen();
            this._logitBias = value;
        }
    }

    /// <summary>
    /// Specifies how the API handles inputs longer than the maximum token length. Use one of the following: NONE, START, or END.
    /// </summary>
    [JsonPropertyName("truncate")]
    public string? Truncate
    {
        get => this._truncate;
        set
        {
            this.ThrowIfFrozen();
            this._truncate = value;
        }
    }

    /// <summary>
    /// Converts PromptExecutionSettings to AmazonCommandExecutionSettings
    /// </summary>
    /// <param name="executionSettings">The Kernel standard PromptExecutionSettings.</param>
    /// <returns>Model specific execution settings</returns>
    public static AmazonCommandExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AmazonCommandExecutionSettings();
            case AmazonCommandExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<AmazonCommandExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}
