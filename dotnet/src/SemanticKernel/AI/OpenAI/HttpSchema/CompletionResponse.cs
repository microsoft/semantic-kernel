// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;

/// <summary>
/// Completion Response
/// </summary>
public sealed class CompletionResponse
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
    }

    /// <summary>
    /// List of possible completions.
    /// </summary>
    [JsonPropertyName("choices")]
    public IList<Choice> Completions { get; set; } = new List<Choice>();
}
