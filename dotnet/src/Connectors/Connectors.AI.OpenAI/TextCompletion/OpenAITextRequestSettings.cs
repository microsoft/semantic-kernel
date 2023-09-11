// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;

/// <summary>
/// Request settings for an OpenAI text completion request.
/// </summary>
public class OpenAITextRequestSettings
{
    private static readonly double DefaultTemperature = 0;
    private static readonly double DefaultTopP = 0;
    private static readonly double DefaultPresencePenalty = 0;
    private static readonly double DefaultFrequencyPenalty = 0;
    private static readonly int DefaultMaxTokens = 256;
    private static readonly IList<string> DefaultStopSequences = Array.Empty<string>();
    private static readonly int DefaultResultsPerPrompt = 1;
    private static readonly string DefaultChatSystemPrompt = "Assistant is a large language model.";
    private static readonly IDictionary<int, int> DefaultTokenSelectionBiases = new Dictionary<int, int>();

    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// </summary>
    public double Temperature { get; set; } = DefaultTemperature;

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// </summary>
    public double TopP { get; set; } = DefaultTopP;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    public double PresencePenalty { get; set; } = DefaultPresencePenalty;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    public double FrequencyPenalty { get; set; } = DefaultFrequencyPenalty;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int? MaxTokens { get; set; } = DefaultMaxTokens;

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    public IList<string> StopSequences { get; set; } = DefaultStopSequences;

    /// <summary>
    /// How many completions to generate for each prompt. Default is 1.
    /// Note: Because this parameter generates many completions, it can quickly consume your token quota.
    /// Use carefully and ensure that you have reasonable settings for max_tokens and stop.
    /// </summary>
    public int ResultsPerPrompt { get; set; } = DefaultResultsPerPrompt;

    /// <summary>
    /// The system prompt to use when generating text completions using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    public string ChatSystemPrompt { get; set; } = DefaultChatSystemPrompt;

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    public IDictionary<int, int> TokenSelectionBiases { get; set; } = DefaultTokenSelectionBiases;

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="requestSettings">Template configuration</param>
    /// <returns>An instance of <see cref="OpenAITextRequestSettings"/></returns>
    public static OpenAITextRequestSettings FromRequestSettings(dynamic? requestSettings)
    {
        if (requestSettings is null)
        {
            return new OpenAITextRequestSettings();
        }

        if (requestSettings.GetType() == typeof(OpenAITextRequestSettings))
        {
            return (OpenAITextRequestSettings)requestSettings;
        }

        var settings = new OpenAITextRequestSettings
        {
            Temperature = DynamicUtils.TryGetPropertyValue<double>(requestSettings, "Temperature", DefaultTemperature),
            TopP = DynamicUtils.TryGetPropertyValue<double>(requestSettings, "TopP", DefaultTopP),
            PresencePenalty = DynamicUtils.TryGetPropertyValue<double>(requestSettings, "PresencePenalty", DefaultPresencePenalty),
            FrequencyPenalty = DynamicUtils.TryGetPropertyValue<double>(requestSettings, "FrequencyPenalty", DefaultFrequencyPenalty),
            MaxTokens = DynamicUtils.TryGetPropertyValue<int?>(requestSettings, "MaxTokens", DefaultMaxTokens),
            StopSequences = DynamicUtils.TryGetPropertyValue<IList<string>>(requestSettings, "StopSequences", DefaultStopSequences),
            ChatSystemPrompt = DynamicUtils.TryGetPropertyValue<string?>(requestSettings, "ChatSystemPrompt", DefaultChatSystemPrompt),
            TokenSelectionBiases = DynamicUtils.TryGetPropertyValue<IDictionary<int, int>?>(requestSettings, "TokenSelectionBiases", DefaultTokenSelectionBiases)
        };

        return settings;
    }
}
