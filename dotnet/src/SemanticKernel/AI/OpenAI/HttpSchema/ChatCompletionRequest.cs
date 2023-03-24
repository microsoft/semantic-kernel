// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Security.Cryptography.X509Certificates;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;

/// <summary>
/// Completion Request
/// </summary>
public abstract class ChatCompletionRequest
{
    /// <summary>
    /// What sampling temperature to use. Higher values means the model will take more risks. Try 0.9 for more creative
    /// applications, and 0 (argmax sampling) for ones with a well-defined answer. It is generally recommend to use this
    /// or "TopP" but not both.
    /// </summary>

    [JsonPropertyName("temperature")]
    [JsonPropertyOrder(1)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? Temperature { get; set; }

    /// <summary>
    /// An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of
    /// the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are
    /// considered. It is generally recommend to use this or "Temperature" but not both.
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonPropertyOrder(2)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? TopP { get; set; }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so
    /// far, increasing the model's likelihood to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    [JsonPropertyOrder(3)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? PresencePenalty { get; set; }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text
    /// so far, decreasing the model's likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    [JsonPropertyOrder(4)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? FrequencyPenalty { get; set; }

    /// <summary>
    /// How many tokens to complete to. Can return fewer if a stop sequence is hit.
    /// The token count of your prompt plus max_tokens cannot exceed the model's context length. Most models have a
    /// context length of 2048 tokens (except for the newest models, which support 4096).
    /// </summary>
    [JsonPropertyName("max_tokens")]
    [JsonPropertyOrder(5)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxTokens { get; set; } = 16;

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
    /// A unique identifier representing your end-user, which can help Azure / OpenAI to monitor and detect abuse.
    /// </summary>
    [JsonPropertyName("user")]
    [JsonPropertyOrder(8)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string User { get; set; } = string.Empty;

    /// <summary>
    /// The messages to generate chat completions for, encoded as a string, array of strings, array of tokens, or array of token arrays
    /// </summary>
    [JsonPropertyName("messages")]
    [JsonPropertyOrder(100)]
    public JsonArray Messages { get; set; } = new JsonArray();

}


/// <summary>
/// OpenAI Completion Request
/// </summary>
public sealed class OpenAIChatCompletionRequest : ChatCompletionRequest
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
public sealed class AzureChatCompletionRequest : ChatCompletionRequest
{
}
