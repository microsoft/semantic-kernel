// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents embedding content.
/// </summary>
/// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
[Experimental("SKEXP0001")]
public sealed class EmbeddingContent<TEmbedding> : KernelContent where TEmbedding : unmanaged
{
    /// <summary>
    /// Represents embedding content.
    /// </summary>
    /// <param name="innerContent">Inner content</param>
    /// <param name="data">The embedding data</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    public EmbeddingContent(
        object? innerContent,
        IReadOnlyList<ReadOnlyMemory<TEmbedding>> data,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Data = data;
    }

    /// <summary>
    /// Represents embedding content.
    /// </summary>
    public IReadOnlyList<ReadOnlyMemory<TEmbedding>> Data { get; set; }
}
