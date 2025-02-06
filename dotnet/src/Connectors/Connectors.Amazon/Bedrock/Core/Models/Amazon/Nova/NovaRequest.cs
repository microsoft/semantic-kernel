// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Nova;

internal static class NovaRequest
{
    /// <summary>
    /// The Nova Text Generation Request object.
    /// </summary>
    internal sealed class NovaTextGenerationRequest
    {
        /// <summary>
        /// Schema version for the request, defaulting to "messages-v1".
        /// </summary>
        [JsonPropertyName("schemaVersion")]
        public string SchemaVersion { get; set; } = "messages-v1";

        /// <summary>
        /// System messages providing context for the generation.
        /// </summary>
        [JsonPropertyName("system")]
        public IList<NovaSystemMessage>? System { get; set; }

        /// <summary>
        /// User messages for text generation.
        /// </summary>
        [JsonPropertyName("messages")]
        public IList<NovaUserMessage>? Messages { get; set; }

        /// <summary>
        /// Text generation configurations as required by Nova request body.
        /// </summary>
        [JsonPropertyName("inferenceConfig")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public NovaTextGenerationConfig? InferenceConfig { get; set; }
    }

    /// <summary>
    /// Represents a system message.
    /// </summary>
    internal sealed class NovaSystemMessage
    {
        /// <summary>
        /// The text of the system message.
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }
    }

    /// <summary>
    /// Represents a user message.
    /// </summary>
    internal sealed class NovaUserMessage
    {
        /// <summary>
        /// The role of the message sender.
        /// </summary>
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        /// <summary>
        /// The content of the user message.
        /// </summary>
        [JsonPropertyName("content")]
        public IList<NovaUserMessageContent>? Content { get; set; } = new List<NovaUserMessageContent>();
    }

    /// <summary>
    /// Represents the content of a user message.
    /// </summary>
    internal sealed class NovaUserMessageContent
    {
        /// <summary>
        /// The text of the user message content.
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }
    }

    /// <summary>
    /// Nova Text Generation Configurations.
    /// </summary>
    internal sealed class NovaTextGenerationConfig
    {
        /// <summary>
        /// Maximum new tokens to generate in the response.
        /// </summary>
        [JsonPropertyName("max_new_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxNewTokens { get; set; }

        /// <summary>
        /// Top P controls token choices, based on the probability of the potential choices. The range is 0 to 1. The default is 1.
        /// </summary>
        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? TopP { get; set; }

        /// <summary>
        /// Top K limits the number of token options considered at each generation step. The default is 20.
        /// </summary>
        [JsonPropertyName("top_k")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? TopK { get; set; }

        /// <summary>
        /// The Temperature value ranges from 0 to 1, with 0 being the most deterministic and 1 being the most creative.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? Temperature { get; set; }
    }
}
