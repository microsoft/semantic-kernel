// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Bedrock.Core.Models.AI21Labs;

/// <summary>
/// The AI21 Labs Jurassic request object.
/// </summary>
internal static class AI21JurassicRequest
{
    /// <summary>
    /// The AI21 Labs Jurassic Text Generation request object.
    /// </summary>
    [Serializable]
    public class AI21JurassicTextGenerationRequest
    {
        /// <summary>
        /// The input prompt as required by AI21 Labs Jurassic.
        /// </summary>
        [JsonPropertyName("prompt")]
        public required string Prompt { get; set; }
        /// <summary>
        /// Use a lower value to decrease randomness in the response.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }
        /// <summary>
        /// Use a lower value to ignore less probable options.
        /// </summary>
        [JsonPropertyName("topP")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }
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
        public CountPenalty? CountPenalty { get; set; }
        /// <summary>
        /// Use a higher value to lower the probability of generating new tokens that already appear at least once in the prompt or in the completion.
        /// </summary>
        [JsonPropertyName("presencePenalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public PresencePenalty? PresencePenalty { get; set; }
        /// <summary>
        /// Use a high value to lower the probability of generating new tokens that already appear at least once in the prompt or in the completion. The value is proportional to the frequency of the token appearances (normalized to text length).
        /// </summary>
        [JsonPropertyName("frequencyPenalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public FrequencyPenalty? FrequencyPenalty { get; set; }
    }
    /// <summary>
    /// Fields that can be added to the penalty objects.
    /// </summary>
    [Serializable]
    public class CountPenalty
    {
        /// <summary>
        /// Scale of the penalty.
        /// </summary>
        [JsonPropertyName("scale")]
        public double Scale { get; set; }
        /// <summary>
        /// Whether to apply penalty to white spaces.
        /// </summary>
        [JsonPropertyName("applyToWhitespaces")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToWhitespaces { get; set; }
        /// <summary>
        /// Whether to apply penalty to punctuation.
        /// </summary>
        [JsonPropertyName("applyToPunctuations")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToPunctuations { get; set; }
        /// <summary>
        /// Whether to apply penalty to numbers.
        /// </summary>
        [JsonPropertyName("applyToNumbers")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToNumbers { get; set; }
        /// <summary>
        /// Whether to apply penalty to stop words.
        /// </summary>
        [JsonPropertyName("applyToStopwords")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToStopwords { get; set; }
        /// <summary>
        /// Whether to apply penalty to emojis.
        /// </summary>
        [JsonPropertyName("applyToEmojis")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToEmojis { get; set; }
    }
    /// <summary>
    /// Fields that can be added to the penalty objects.
    /// </summary>
    [Serializable]
    public class PresencePenalty
    {
        /// <summary>
        /// Scale of the penalty.
        /// </summary>
        [JsonPropertyName("scale")]
        public double Scale { get; set; }

        /// <summary>
        /// Whether to apply penalty to white spaces.
        /// </summary>
        [JsonPropertyName("applyToWhitespaces")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToWhitespaces { get; set; }

        /// <summary>
        /// Whether to apply penalty to punctuation.
        /// </summary>
        [JsonPropertyName("applyToPunctuations")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToPunctuations { get; set; }

        /// <summary>
        /// Whether to apply penalty to numbers.
        /// </summary>
        [JsonPropertyName("applyToNumbers")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToNumbers { get; set; }

        /// <summary>
        /// Whether to apply penalty to stop words.
        /// </summary>
        [JsonPropertyName("applyToStopwords")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToStopwords { get; set; }

        /// <summary>
        /// Whether to apply penalty to emojis.
        /// </summary>
        [JsonPropertyName("applyToEmojis")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToEmojis { get; set; }
    }

    /// <summary>
    /// Fields that can be added to the penalty objects.
    /// </summary>
    [Serializable]
    public class FrequencyPenalty
    {
        /// <summary>
        /// Scale of the penalty.
        /// </summary>
        [JsonPropertyName("scale")]
        public double Scale { get; set; }

        /// <summary>
        /// Whether to apply penalty to white spaces.
        /// </summary>
        [JsonPropertyName("applyToWhitespaces")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToWhitespaces { get; set; }

        /// <summary>
        /// Whether to apply penalty to punctuation.
        /// </summary>
        [JsonPropertyName("applyToPunctuations")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToPunctuations { get; set; }

        /// <summary>
        /// Whether to apply penalty to numbers.
        /// </summary>
        [JsonPropertyName("applyToNumbers")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToNumbers { get; set; }

        /// <summary>
        /// Whether to apply penalty to stop words.
        /// </summary>
        [JsonPropertyName("applyToStopwords")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToStopwords { get; set; }

        /// <summary>
        /// Whether to apply penalty to emojis.
        /// </summary>
        [JsonPropertyName("applyToEmojis")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ApplyToEmojis { get; set; }
    }
}
