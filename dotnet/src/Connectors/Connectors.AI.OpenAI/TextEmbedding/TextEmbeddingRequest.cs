// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;

/// <summary>
/// A request to create embedding vector representing input text
/// </summary>
public abstract class TextEmbeddingRequest
{
    /// <summary>
    /// Input to embed
    /// </summary>
    [JsonPropertyName("input")]
    public IList<string> Input { get; set; } = new List<string>();
}

/// <summary>
/// An OpenAI embedding request
/// </summary>
public sealed class OpenAITextEmbeddingRequest : TextEmbeddingRequest
{
    /// <summary>
    /// Embedding model ID
    /// </summary>
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;
}

/// <summary>
/// An Azure OpenAI embedding request
/// </summary>
public sealed class AzureTextEmbeddingRequest : TextEmbeddingRequest
{
}
