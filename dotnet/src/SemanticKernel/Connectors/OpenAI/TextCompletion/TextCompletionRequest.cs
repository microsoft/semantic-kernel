// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI.TextCompletion;

/// <summary>
/// Text Completion Request
/// </summary>
public abstract class TextCompletionRequest
{
    /// <summary>
    /// What sampling temperature to use. Higher values means the model will take
    /// more risks. Try 0.9 for more creative applications, and 0 (argmax sampling)
    /// for ones with a well-defined answer. It is generally recommend to use this
    /// or "TopP" but not both.
    /// </summary>
    [JsonPropertyName("temperature")]
    [JsonPropertyOrder(1)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? Temperature { get; set; }

    /// <summary>
    /// An alternative to sampling with temperature, called nucleus sampling, where
    /// the model considers the results of the tokens with top_p probability mass.
    /// So 0.1 means only the tokens comprising the top 10% probability mass are
    /// considered. It is generally recommend to use this or "Temperature" but not both.
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonPropertyOrder(2)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? TopP { get; set; }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based
    /// on whether they appear in the text so far, increasing the model's likelihood
    /// to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    [JsonPropertyOrder(3)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? PresencePenalty { get; set; }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based
    /// on their existing frequency in the text so far, decreasing the model's
    /// likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    [JsonPropertyOrder(4)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? FrequencyPenalty { get; set; }

    /// <summary>
    /// How many tokens to complete to. Can return fewer if a stop sequence is hit.
    /// The token count of your prompt plus max_tokens cannot exceed the model's context
    /// length. Depending on the models this typically varies from 1k to 32k.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    [JsonPropertyOrder(5)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxTokens { get; set; } = 256;

    /// <summary>
    /// Up to 4 sequences where the API will stop generating further tokens.
    /// The returned text will not contain the stop sequence.
    /// Type: string or array of strings
    /// </summary>
    [JsonPropertyName("stop")]
    [JsonPropertyOrder(6)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Stop { get; set; }

    /// <summary>
    /// How many different choices to request for each prompt.
    /// Note: Because this parameter generates many completions, it can quickly consume your token quota.
    /// </summary>
    [JsonPropertyName("n")]
    [JsonPropertyOrder(7)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? NumChoices { get; set; } = 1;

    /// <summary>
    /// Generates best_of completions server-side and returns the "best"
    /// (the one with the highest log probability per token).
    /// When used with NumChoices, BestOf controls the number of candidate completions and NumChoices specifies
    /// how many to return. BestOf must be greater than NumChoices
    /// </summary>
    [JsonPropertyName("best_of")]
    [JsonPropertyOrder(8)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? BestOf { get; set; } = 1;

    /// <summary>
    /// The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays
    /// </summary>
    [JsonPropertyName("prompt")]
    [JsonPropertyOrder(100)]
    public string Prompt { get; set; } = string.Empty;
}

/// <summary>
/// OpenAI Completion Request
/// </summary>
public sealed class OpenAITextCompletionRequest : TextCompletionRequest
{
    /// <summary>
    /// ID of the model to use.
    /// </summary>
    [JsonPropertyName("model")]
    [JsonPropertyOrder(-1)]
    public string? Model { get; set; }
}

/// <summary>
/// Azure OpenAI Completion Request
/// </summary>
public sealed class AzureTextCompletionRequest : TextCompletionRequest
{
}
