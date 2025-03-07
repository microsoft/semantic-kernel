// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ChatWithAgent.Configuration;

/// <summary>
/// Contains settings to control the RAG experience.
/// </summary>
public sealed class RagConfig
{
    /// <summary>
    /// The AI embeddings service to use.
    /// </summary>
    [Required]
    public string AIEmbeddingService { get; set; } = string.Empty;

    /// <summary>
    /// Type of the vector store.
    /// </summary>
    [Required]
    public string VectorStoreType { get; set; } = string.Empty;
}
