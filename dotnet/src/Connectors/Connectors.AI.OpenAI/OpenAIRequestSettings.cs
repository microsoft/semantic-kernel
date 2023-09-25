// Copyright (c) Microsoft. All rights reserved.

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// Request settings for an OpenAI completion request.
/// </summary>
public class OpenAIRequestSettings : AIRequestSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// </summary>
    [JsonPropertyName("temperature")]
    [JsonPropertyOrder(1)]
    public double Temperature { get; set; } = 0;

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonPropertyOrder(2)]
    public double TopP { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    [JsonPropertyOrder(3)]
    public double PresencePenalty { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    [JsonPropertyOrder(4)]
    public double FrequencyPenalty { get; set; } = 0;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    [JsonPropertyOrder(5)]
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    [JsonPropertyOrder(6)]
    public IList<string> StopSequences { get; set; } = Array.Empty<string>();

    /// <summary>
    /// How many completions to generate for each prompt. Default is 1.
    /// Note: Because this parameter generates many completions, it can quickly consume your token quota.
    /// Use carefully and ensure that you have reasonable settings for max_tokens and stop.
    /// </summary>
    [JsonPropertyName("results_per_prompt")]
    [JsonPropertyOrder(7)]
    public int ResultsPerPrompt
    {
        get
        {
            if (this.ExtensionData.TryGetValue("results_per_prompt", out var value))
            {
                return (int)value;
            }

            return 1;
        }
        set
        {
            this.ExtensionData["results_per_prompt"] = value;
        }
    }

    /// <summary>
    /// The system prompt to use when generating text completions using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    [JsonPropertyName("chat_system_prompt")]
    [JsonPropertyOrder(8)]
    public string ChatSystemPrompt
    {
        get => this._chatSystemPrompt;
        set
        {
            if (string.IsNullOrEmpty(value))
            {
                value = OpenAIRequestSettings.DefaultChatSystemPrompt;
            }
            this._chatSystemPrompt = value;
        }
    }

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    [JsonPropertyName("token_selection_biases")]
    [JsonPropertyOrder(9)]
    public IDictionary<int, int> TokenSelectionBiases { get; set; } = new Dictionary<int, int>();

    /// <summary>
    /// Default value for chat system property.
    /// </summary>
    internal static string DefaultChatSystemPrompt { get; } = "Assistant is a large language model.";

    /// <summary>
    /// Default max tokens for a chat completion
    /// </summary>
    internal static int DefaultTextMaxTokens { get; } = 256;

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="requestSettings">Template configuration</param>
    /// <param name="defaultMaxTokens">Default max tokens</param>
    /// <returns>An instance of OpenAIRequestSettings</returns>
    public static OpenAIRequestSettings FromRequestSettings(AIRequestSettings? requestSettings, int? defaultMaxTokens = null)
    {
        if (requestSettings is null)
        {
            return new OpenAIRequestSettings()
            {
                MaxTokens = defaultMaxTokens
            };
        }

        if (requestSettings is OpenAIRequestSettings requestSettingsOpenAIRequestSettings)
        {
            return requestSettingsOpenAIRequestSettings;
        }

        var json = JsonSerializer.Serialize(requestSettings);
        var openAIRequestSettings = JsonSerializer.Deserialize<OpenAIRequestSettings>(json, s_options);

        if (openAIRequestSettings is not null)
        {
            return openAIRequestSettings;
        }

        throw new ArgumentException($"Invalid request settings, cannot convert to {nameof(OpenAIRequestSettings)}", nameof(requestSettings));
    }

    #region private ================================================================================

    private string _chatSystemPrompt = OpenAIRequestSettings.DefaultChatSystemPrompt;

    private static readonly JsonSerializerOptions s_options = CreateOptions();

    private static JsonSerializerOptions CreateOptions()
    {
        JsonSerializerOptions options = new()
        {
            WriteIndented = true,
            MaxDepth = 20,
            AllowTrailingCommas = true,
            PropertyNameCaseInsensitive = true,
            ReadCommentHandling = JsonCommentHandling.Skip,
            Converters = { new OpenAIRequestSettingsConverter() }
        };

        return options;
    }

    #endregion
}
