// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Backends.HuggingFace.HttpSchema;

/// <summary>
/// HTTP Schema for completion response.
/// </summary>
public sealed class CompletionResponse
{
    /// <summary>
    /// Model containing possible completion option.
    /// </summary>
    public sealed class Choice
    {
        /// <summary>
        /// Completed text.
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }
    }

    /// <summary>
    /// List of possible completions.
    /// </summary>
    [JsonPropertyName("choices")]
    public IList<Choice>? Choices { get; set; }
}
