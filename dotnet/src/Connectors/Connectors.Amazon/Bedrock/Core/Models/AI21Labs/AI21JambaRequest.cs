// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Request object for AI21 Jamba.
/// </summary>
internal static class AI21JambaRequest
{
    /// <summary>
    /// Text Generation Request object for AI21 Jamba.
    /// </summary>
    internal sealed class AI21TextGenerationRequest
    {
        /// <summary>
        /// The previous messages in this chat, from oldest (index 0) to newest. Must have at least one user or assistant message in the list. Include both user inputs and system responses. Maximum total size for the list is about 256K tokens.
        /// </summary>
        [JsonPropertyName("messages")]
        public List<JambaMessage> Messages { get; set; } = [];

        /// <summary>
        /// How many responses to generate (one for text generation).
        /// </summary>
        [JsonPropertyName("n")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? NumberOfResponses { get; set; }

        /// <summary>
        /// How much variation to provide in each answer. Setting this value to 0 guarantees the same response to the same question every time. Setting a higher value encourages more variation. Modifies the distribution from which tokens are sampled. Default: 1.0, Range: 0.0 – 2.0
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? Temperature { get; set; }

        /// <summary>
        /// Limit the pool of next tokens in each step to the top N percentile of possible tokens, where 1.0 means the pool of all possible tokens, and 0.01 means the pool of only the most likely next tokens.
        /// </summary>
        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? TopP { get; set; }

        /// <summary>
        /// The maximum number of tokens to allow for each generated response message. Typically, the best way to limit output length is by providing a length limit in the system prompt (for example, "limit your answers to three sentences"). Default: 4096, Range: 0 – 4096.
        /// </summary>
        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        /// <summary>
        /// End the message when the model generates one of these strings. The stop sequence is not included in the generated message. Each sequence can be up to 64K long, and can contain newlines as \n characters.
        /// </summary>
        [JsonPropertyName("stop")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? Stop { get; set; }

        /// <summary>
        /// Reduce frequency of repeated words within a single response message by increasing this number. This penalty gradually increases the more times a word appears during response generation. Setting to 2.0 will produce a string with few, if any repeated words.
        /// </summary>
        [JsonPropertyName("frequency_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? FrequencyPenalty { get; set; }

        /// <summary>
        /// Reduce the frequency of repeated words within a single message by increasing this number. Unlike frequency penalty, presence penalty is the same no matter how many times a word appears.
        /// </summary>
        [JsonPropertyName("presence_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? PresencePenalty { get; set; }

        /// <summary>
        /// Message object for AI21 Labs Jamba which has the role and content.
        /// </summary>
        internal sealed class JambaMessage
        {
            /// <summary>
            /// Role of the message written (assistant, user, or system).
            /// </summary>
            [JsonPropertyName("role")]
            public string? Role { get; set; }

            /// <summary>
            /// Message contents.
            /// </summary>
            [JsonPropertyName("content")]
            public string? Content { get; set; }
        }
    }
}
