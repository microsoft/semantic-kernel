// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal static class TitanRequest
{
    /// <summary>
    /// The Amazon Titan Text Generation Request object.
    /// </summary>
    internal sealed class TitanTextGenerationRequest
    {
        /// <summary>
        /// The provided input text string for text generation response.
        /// </summary>
        [JsonPropertyName("inputText")]
        public string? InputText { get; set; }

        /// <summary>
        /// Text generation configurations as required by Amazon Titan request body.
        /// </summary>
        [JsonPropertyName("textGenerationConfig")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public AmazonTitanTextGenerationConfig? TextGenerationConfig { get; set; }
    }

    /// <summary>
    /// Amazon Titan Text Generation Configurations.
    /// </summary>
    internal sealed class AmazonTitanTextGenerationConfig
    {
        /// <summary>
        /// Top P controls token choices, based on the probability of the potential choices. The range is 0 to 1. The default is 1.
        /// </summary>
        [JsonPropertyName("topP")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? TopP { get; set; }

        /// <summary>
        /// The Temperature value ranges from 0 to 1, with 0 being the most deterministic and 1 being the most creative.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? Temperature { get; set; }

        /// <summary>
        /// Configures the maximum number of tokens in the generated response. The range is 0 to 4096. The default is 512.
        /// </summary>
        [JsonPropertyName("maxTokenCount")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokenCount { get; set; }

        /// <summary>
        /// Use | (pipe) characters (maximum 20 characters).
        /// </summary>
        [JsonPropertyName("stopSequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; } = [];
    }
}
