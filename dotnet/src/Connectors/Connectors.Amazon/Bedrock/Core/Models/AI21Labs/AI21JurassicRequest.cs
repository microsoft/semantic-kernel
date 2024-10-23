// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// The AI21 Labs Jurassic request object.
/// </summary>
internal static class AI21JurassicRequest
{
    /// <summary>
    /// The AI21 Labs Jurassic Text Generation request object.
    /// </summary>
    internal sealed class AI21JurassicTextGenerationRequest
    {
        /// <summary>
        /// The input prompt as required by AI21 Labs Jurassic.
        /// </summary>
        [JsonPropertyName("prompt")]
        public string? Prompt { get; set; }

        /// <summary>
        /// Use a lower value to decrease randomness in the response.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? Temperature { get; set; }

        /// <summary>
        /// Use a lower value to ignore less probable options.
        /// </summary>
        [JsonPropertyName("topP")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? TopP { get; set; }

        /// <summary>
        /// Specify the maximum number of tokens to use in the generated response.
        /// </summary>
        [JsonPropertyName("maxTokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        /// <summary>
        /// Configure stop sequences that the model recognizes and after which it stops generating further tokens. Press the Enter key to insert a newline character in a stop sequence. Use the Tab key to finish inserting a stop sequence.
        /// </summary>
        [JsonPropertyName("stopSequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; }

        /// <summary>
        /// Use a higher value to lower the probability of generating new tokens that already appear at least once in the prompt or in the completion. Proportional to the number of appearances.
        /// </summary>
        [JsonPropertyName("countPenalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public AI21JurassicPenalties? CountPenalty { get; set; }

        /// <summary>
        /// Use a higher value to lower the probability of generating new tokens that already appear at least once in the prompt or in the completion.
        /// </summary>
        [JsonPropertyName("presencePenalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public AI21JurassicPenalties? PresencePenalty { get; set; }

        /// <summary>
        /// Use a high value to lower the probability of generating new tokens that already appear at least once in the prompt or in the completion. The value is proportional to the frequency of the token appearances (normalized to text length).
        /// </summary>
        [JsonPropertyName("frequencyPenalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public AI21JurassicPenalties? FrequencyPenalty { get; set; }
    }
}
