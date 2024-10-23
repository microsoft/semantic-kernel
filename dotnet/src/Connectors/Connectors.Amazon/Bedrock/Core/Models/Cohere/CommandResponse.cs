// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// The Command Text Generation Response body.
/// </summary>
internal sealed class CommandResponse
{
    /// <summary>
    /// A list of generated results along with the likelihoods for tokens requested. (Always returned).
    /// </summary>
    [JsonPropertyName("generations")]
    public List<Generation> Generations { get; set; } = [];

    /// <summary>
    /// An identifier for the request (always returned).
    /// </summary>
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    /// <summary>
    /// The prompt from the input request (always returned).
    /// </summary>
    [JsonPropertyName("prompt")]
    public string? Prompt { get; set; }

    /// <summary>
    /// A list of generated results along with the likelihoods for tokens requested. (Always returned). Each generation object in the list contains the following fields.
    /// </summary>
    internal sealed class Generation
    {
        /// <summary>
        /// The reason why the model finished generating tokens. COMPLETE - the model sent back a finished reply. MAX_TOKENS – the reply was cut off because the model reached the maximum number of tokens for its context length. ERROR – something went wrong when generating the reply. ERROR_TOXIC – the model generated a reply that was deemed toxic. finish_reason is returned only when is_finished=true. (Not always returned).
        /// </summary>
        [JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }

        /// <summary>
        /// An identifier for the generation. (Always returned).
        /// </summary>
        [JsonPropertyName("id")]
        public string? Id { get; set; }

        /// <summary>
        /// The generated text.
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }

        /// <summary>
        /// The likelihood of the output. The value is the average of the token likelihoods in token_likelihoods. Returned if you specify the return_likelihoods input parameter.
        /// </summary>
        [JsonPropertyName("likelihood")]
        public double? Likelihood { get; set; }

        /// <summary>
        /// An array of per token likelihoods. Returned if you specify the return_likelihoods input parameter.
        /// </summary>
        [JsonPropertyName("token_likelihoods")]
        public List<TokenLikelihood>? TokenLikelihoods { get; set; }

        /// <summary>
        /// A boolean field used only when stream is true, signifying whether there are additional tokens that will be generated as part of the streaming response. (Not always returned)
        /// </summary>
        [JsonPropertyName("is_finished")]
        public bool IsFinished { get; set; }

        /// <summary>
        /// In a streaming response, use to determine which generation a given token belongs to. When only one response is streamed, all tokens belong to the same generation and index is not returned. index therefore is only returned in a streaming request with a value for num_generations that is larger than one.
        /// </summary>
        [JsonPropertyName("index")]
        public int? Index { get; set; }
    }

    /// <summary>
    /// An array of per token likelihoods. Returned if you specify the return_likelihoods input parameter.
    /// </summary>
    internal sealed class TokenLikelihood
    {
        /// <summary>
        /// Token likelihood.
        /// </summary>
        [JsonPropertyName("token")]
        public double Token { get; set; }
    }
}
