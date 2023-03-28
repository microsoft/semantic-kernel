// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;

/// <summary>
/// Text completion response
/// </summary>
public sealed class TextCompletionResponse
{
    /// <summary>
    /// A choice of completion response
    /// </summary>
    public sealed class Choice
    {
        /// <summary>
        /// The completed text from the completion request.
        /// </summary>
        [JsonPropertyName("text")]
        public string Text { get; set; } = string.Empty;

        /// <summary>
        /// Index of the choice
        /// </summary>
        [JsonPropertyName("index")]
        public int Index { get; set; } = 0;

        /// <summary>
        /// OpenAI finish reason
        /// </summary>
        [JsonPropertyName("finish_reason")]
        public string FinishReason { get; set; } = string.Empty;
    }

    /// <summary>
    /// OpenAI usage report
    /// </summary>
    public sealed class UsageReport
    {
        /// <summary>
        /// Tokens used in the request
        /// </summary>
        [JsonPropertyName("prompt_tokens")]
        public int PromptTokens { get; set; } = -1;

        /// <summary>
        /// Tokens used by the response
        /// </summary>
        [JsonPropertyName("completion_tokens")]
        public int CompletionTokens { get; set; } = -1;

        /// <summary>
        /// Total tokens used
        /// </summary>
        [JsonPropertyName("total_tokens")]
        public int TotalTokens { get; set; } = -1;
    }

    /// <summary>
    /// List of possible completions.
    /// </summary>
    [JsonPropertyName("choices")]
    public IList<Choice> Completions { get; set; } = new List<Choice>();

    /// <summary>
    /// OpenAI object type
    /// </summary>
    [JsonPropertyName("object")]
    public string ObjectType { get; set; } = string.Empty;

    /// <summary>
    /// Creation time
    /// </summary>
    [JsonPropertyName("created")]
    public int CreatedTime { get; set; }

    /// <summary>
    /// Tokens usage details
    /// </summary>
    [JsonPropertyName("usage")]
    public UsageReport Usage { get; set; } = new UsageReport();
}
