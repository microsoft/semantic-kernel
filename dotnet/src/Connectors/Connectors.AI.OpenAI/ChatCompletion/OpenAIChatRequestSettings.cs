// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/// <summary>
/// Request settings for an OpenAI chat completion request.
/// </summary>
public class OpenAIChatRequestSettings
{
    private static readonly double DefaultTemperature = 0;
    private static readonly double DefaultTopP = 0;
    private static readonly double DefaultPresencePenalty = 0;
    private static readonly double DefaultFrequencyPenalty = 0;
    private static readonly int? DefaultMaxTokens = null;
    private static readonly IList<string> DefaultStopSequences = Array.Empty<string>();
    private static readonly int DefaultResultsPerPrompt = 1;
    private static readonly string DefaultChatSystemPrompt = "Assistant is a large language model.";
    private static readonly IDictionary<int, int> DefaultTokenSelectionBiases = new Dictionary<int, int>();

    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// </summary>
    [JsonPropertyName("temperature")]
    [JsonPropertyOrder(1)]
    public double Temperature { get; set; } = DefaultTemperature;

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonPropertyOrder(2)]
    public double TopP { get; set; } = DefaultTopP;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    [JsonPropertyOrder(3)]
    public double PresencePenalty { get; set; } = DefaultPresencePenalty;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    [JsonPropertyOrder(4)]
    public double FrequencyPenalty { get; set; } = DefaultFrequencyPenalty;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    [JsonPropertyOrder(5)]
    public int? MaxTokens { get; set; } = DefaultMaxTokens;

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    [JsonPropertyOrder(6)]
    public IList<string> StopSequences { get; set; } = DefaultStopSequences;

    /// <summary>
    /// How many completions to generate for each prompt. Default is 1.
    /// Note: Because this parameter generates many completions, it can quickly consume your token quota.
    /// Use carefully and ensure that you have reasonable settings for max_tokens and stop.
    /// </summary>
    [JsonPropertyName("results_per_prompt")]
    [JsonPropertyOrder(7)]
    public int ResultsPerPrompt { get; set; } = DefaultResultsPerPrompt;

    /// <summary>
    /// The system prompt to use when generating text completions using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    [JsonPropertyName("chat_system_prompt")]
    [JsonPropertyOrder(8)]
    public string ChatSystemPrompt { get; set; } = DefaultChatSystemPrompt;

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    [JsonPropertyName("token_selection_biases")]
    [JsonPropertyOrder(9)]
    public IDictionary<int, int> TokenSelectionBiases { get; set; } = DefaultTokenSelectionBiases;

    /// <summary>
    /// Service identifier.
    /// </summary>
    [JsonPropertyName("service_id")]
    [JsonPropertyOrder(10)]
    public string? ServiceId { get; set; } = null;

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="requestSettings">Template configuration</param>
    /// <returns>An instance of <see cref="OpenAITextRequestSettings"/></returns>
    public static OpenAIChatRequestSettings FromRequestSettings(dynamic? requestSettings)
    {
        if (requestSettings is null)
        {
            return new OpenAIChatRequestSettings();
        }

        if (requestSettings.GetType() == typeof(OpenAIChatRequestSettings))
        {
            return (OpenAIChatRequestSettings)requestSettings;
        }

        if (requestSettings.GetType() == typeof(JsonElement))
        {
            return Json.Deserialize<OpenAIChatRequestSettings>(requestSettings.ToString());
        }

        return Json.Deserialize<OpenAIChatRequestSettings>(JsonSerializer.Serialize(requestSettings));
    }
}
