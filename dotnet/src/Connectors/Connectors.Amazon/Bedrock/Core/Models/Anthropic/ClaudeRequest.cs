// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal static class ClaudeRequest
{
    internal sealed class ClaudeTextGenerationRequest
    {
        /// <summary>
        /// (Required) The prompt that you want Claude to complete. For proper response generation you need to format your prompt using alternating \n\nHuman: and \n\nAssistant: conversational turns.
        /// </summary>
        [JsonPropertyName("prompt")]
        public string? Prompt { get; set; }

        /// <summary>
        /// (Required) The maximum number of tokens to generate before stopping. We recommend a limit of 4,000 tokens for optimal performance.
        /// </summary>
        [JsonPropertyName("max_tokens_to_sample")]
        public int MaxTokensToSample { get; set; }

        /// <summary>
        /// (Optional) Sequences that will cause the model to stop generating. Anthropic Claude models stop on "\n\nHuman:", and may include additional built-in stop sequences in the future.Use the stop_sequences inference parameter to include additional strings that will signal the model to stop generating text.
        /// </summary>
        [JsonPropertyName("stop_sequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; }

        /// <summary>
        /// (Optional) The amount of randomness injected into the response. Use a value closer to 0 for analytical / multiple choice, and a value closer to 1 for creative and generative tasks.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }

        /// <summary>
        /// (Optional) Use nucleus sampling. In nucleus sampling, Anthropic Claude computes the cumulative distribution over all the options for each subsequent token in decreasing probability order and cuts it off once it reaches a particular probability specified by top_p.You should alter either temperature or top_p, but not both.
        /// </summary>
        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        /// <summary>
        /// (Optional) Only sample from the top K options for each subsequent token. Use top_k to remove long tail low probability responses.
        /// </summary>
        [JsonPropertyName("top_k")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? TopK { get; set; }
    }
}
