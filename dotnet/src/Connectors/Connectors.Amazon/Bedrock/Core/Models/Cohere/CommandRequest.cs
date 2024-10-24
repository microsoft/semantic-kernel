// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal static class CommandRequest
{
    /// <summary>
    /// Text generation request object.
    /// </summary>
    internal sealed class CohereCommandTextGenerationRequest
    {
        /// <summary>
        /// The input text that serves as the starting point for generating the response.
        /// </summary>
        [JsonPropertyName("prompt")]
        public string? Prompt { get; set; }

        /// <summary>
        /// Use a lower value to decrease randomness in the response.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }

        /// <summary>
        /// Top P. Use a lower value to ignore less probable options. Set to 0 or 1.0 to disable. If both p and k are enabled, p acts after k.
        /// </summary>
        [JsonPropertyName("p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        /// <summary>
        /// Top K. Specify the number of token choices the model uses to generate the next token. If both p and k are enabled, p acts after k.
        /// </summary>
        [JsonPropertyName("k")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopK { get; set; }

        /// <summary>
        /// Specify the maximum number of tokens to use in the generated response.
        /// </summary>
        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        /// <summary>
        /// Configure up to four sequences that the model recognizes. After a stop sequence, the model stops generating further tokens. The returned text doesn't contain the stop sequence.
        /// </summary>
        [JsonPropertyName("stop_sequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; }

        /// <summary>
        /// Specify how and if the token likelihoods are returned with the response. You can specify the following options: GENERATION, ALL, or NONE.
        /// </summary>
        [JsonPropertyName("return_likelihoods")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? ReturnLikelihoods { get; set; }

        /// <summary>
        /// (Required to support streaming) Specify true to return the response piece-by-piece in real-time and false to return the complete response after the process finishes.
        /// </summary>
        [JsonPropertyName("stream")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? Stream { get; set; }

        /// <summary>
        /// The maximum number of generations that the model should return.
        /// </summary>
        [JsonPropertyName("num_generations")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? NumGenerations { get; set; }

        /// <summary>
        /// Prevents the model from generating unwanted tokens or incentivizes the model to include desired tokens. The format is {token_id: bias} where bias is a float between -10 and 10. Tokens can be obtained from text using any tokenization service, such as Cohere’s Tokenize endpoint.
        /// </summary>
        [JsonPropertyName("logit_bias")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public Dictionary<int, double>? LogitBias { get; set; }

        /// <summary>
        /// Specifies how the API handles inputs longer than the maximum token length. Use one of the following: NONE, START, or END.
        /// </summary>
        [JsonPropertyName("truncate")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Truncate { get; set; }
    }
}
