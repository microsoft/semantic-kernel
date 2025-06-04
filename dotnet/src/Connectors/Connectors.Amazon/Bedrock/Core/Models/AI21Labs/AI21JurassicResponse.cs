// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// AI21 Labs Jurassic Response object.
/// </summary>
internal sealed class AI21JurassicResponse
{
    /// <summary>
    /// A unique string id for the processed request. Repeated identical requests receive different IDs.
    /// </summary>
    [JsonPropertyName("id")]
    public long Id { get; set; }

    /// <summary>
    /// The prompt includes the raw text, the tokens with their log probabilities, and the top-K alternative tokens at each position, if requested.
    /// </summary>
    [JsonPropertyName("prompt")]
    public PromptText? Prompt { get; set; }

    /// <summary>
    /// A list of completions, including raw text, tokens, and log probabilities. The number of completions corresponds to the requested numResults.
    /// </summary>
    [JsonPropertyName("completions")]
    public List<Completion>? Completions { get; set; }

    /// <summary>
    /// The prompt includes the raw text, the tokens with their log probabilities, and the top-K alternative tokens at each position, if requested.
    /// </summary>
    internal sealed class PromptText
    {
        /// <summary>
        /// Text string of the prompt.
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }

        /// <summary>
        /// list of TokenData.
        /// </summary>
        [JsonPropertyName("tokens")]
        public List<Token>? Tokens { get; set; }
    }

    /// <summary>
    /// The token object corresponding to each prompt object.
    /// </summary>
    internal sealed class Token
    {
        /// <summary>
        /// The token object generated from the token data.
        /// </summary>
        [JsonPropertyName("generatedToken")]
        public GeneratedToken? GeneratedToken { get; set; }

        /// <summary>
        /// A list of the top K alternative tokens for this position, sorted by probability, according to the topKReturn request parameter. If topKReturn is set to 0, this field will be null.
        /// </summary>
        [JsonPropertyName("topTokens")]
        public object? TopTokens { get; set; }

        /// <summary>
        /// Indicates the start and end offsets of the token in the decoded text string.
        /// </summary>
        [JsonPropertyName("textRange")]
        public TextRange? TextRange { get; set; }
    }

    /// <summary>
    /// The generated token object from the token data.
    /// </summary>
    internal sealed class GeneratedToken
    {
        /// <summary>
        /// The string representation of the token.
        /// </summary>
        [JsonPropertyName("token")]
        public string? TokenValue { get; set; }

        /// <summary>
        /// The predicted log probability of the token after applying the sampling parameters as a float value.
        /// </summary>
        [JsonPropertyName("logprob")]
        public double Logprob { get; set; }

        /// <summary>
        /// The raw predicted log probability of the token as a float value. For the indifferent values (namely, temperature=1, topP=1) we get raw_logprob=logprob.
        /// </summary>
        [JsonPropertyName("raw_logprob")]
        public double RawLogprob { get; set; }
    }

    /// <summary>
    /// Indicates the start and end offsets of the token in the decoded text string.
    /// </summary>
    internal sealed class TextRange
    {
        /// <summary>
        /// The starting index of the token in the decoded text string.
        /// </summary>
        [JsonPropertyName("start")]
        public int Start { get; set; }

        /// <summary>
        /// The ending index of the token in the decoded text string.
        /// </summary>
        [JsonPropertyName("end")]
        public int End { get; set; }
    }

    /// <summary>
    /// A list of completions, including raw text, tokens, and log probabilities. The number of completions corresponds to the requested numResults.
    /// </summary>
    internal sealed class Completion
    {
        /// <summary>
        /// The data, which contains the text (string) and tokens (list of TokenData) for the completion.
        /// </summary>
        [JsonPropertyName("data")]
        public JurassicData? Data { get; set; }

        /// <summary>
        /// This nested data structure explains the reason of the generation ending.
        /// </summary>
        [JsonPropertyName("finishReason")]
        public FinishReason? FinishReason { get; set; }
    }

    /// <summary>
    /// The data, which contains the text (string) and tokens (list of TokenData) for the completion
    /// </summary>
    internal sealed class JurassicData
    {
        /// <summary>
        /// The text string from the data provided.
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }

        /// <summary>
        /// The list of tokens.
        /// </summary>
        [JsonPropertyName("tokens")]
        public List<Token>? Tokens { get; set; }
    }

    /// <summary>
    /// This nested data structure explains why the generation process was halted for a specific completion.
    /// </summary>
    internal sealed class FinishReason
    {
        /// <summary>
        /// The finish reason: length limit reached, end of text token generation, or stop sequence generated.
        /// </summary>
        [JsonPropertyName("reason")]
        public string? Reason { get; set; }

        /// <summary>
        /// The max token count.
        /// </summary>
        [JsonPropertyName("length")]
        public int Length { get; set; }
    }
}
