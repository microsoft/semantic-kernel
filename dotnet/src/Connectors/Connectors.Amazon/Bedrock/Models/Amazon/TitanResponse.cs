// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models.Amazon;

/// <summary>
/// Amazon Titan Chat Completion Response object.
/// </summary>
public class TitanChatResponse
{
    /// <summary>
    /// The number of tokens in the prompt.
    /// </summary>
    [JsonPropertyName("inputTextTokenCount")]
    public int InputTextTokenCount { get; set; }
    /// <summary>
    /// The result object from the chat completion.
    /// </summary>
    [JsonPropertyName("results")]
    public required IReadOnlyList<AmazonTitanChatCompletionResult> Results { get; set; }
}
/// <summary>
/// Amazon Titan chat completion result object.
/// </summary>
public class AmazonTitanChatCompletionResult : ChatMessageContent
{
    /// <summary>
    /// The number of tokens in the response.
    /// </summary>
    [JsonPropertyName("tokenCount")]
    public int TokenCount { get; set; }
    /// <summary>
    /// The text in the response.
    /// </summary>
    [JsonPropertyName("outputText")]
    public required string OutputText { get; set; }
    /// <summary>
    /// The reason the response finished being generated.
    /// </summary>
    [JsonPropertyName("completionReason")]
    public string? CompletionReason { get; set; }
}

/// <summary>
/// The Amazon Titan Text response object when deserialized from Invoke Model call.
/// </summary>
[Serializable]
public class TitanTextResponse
{
    /// <summary>
    /// The number of tokens in the prompt.
    /// </summary>
    [JsonPropertyName("inputTextTokenCount")]
    public int InputTextTokenCount { get; set; }
    /// <summary>
    /// The list of result objects.
    /// </summary>
    [JsonPropertyName("results")]
    public List<Result>? Results { get; set; }
    /// <summary>
    /// The result object.
    /// </summary>
    public class Result
    {
        /// <summary>
        /// The number of tokens in the prompt.
        /// </summary>
        [JsonPropertyName("tokenCount")]
        public int TokenCount { get; set; }
        /// <summary>
        /// The text in the response.
        /// </summary>
        [JsonPropertyName("outputText")]
        public string? OutputText { get; set; }
        /// <summary>
        /// The reason the response finished being generated.
        /// </summary>
        [JsonPropertyName("completionReason")]
        public string? CompletionReason { get; set; }
    }
}
