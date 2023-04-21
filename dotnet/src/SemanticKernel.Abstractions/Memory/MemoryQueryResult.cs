// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Copy of metadata associated with a memory entry.
/// </summary>
public class MemoryQueryResult
{
    /// <summary>
    /// Whether the source data used to calculate embeddings are stored in the local
    /// storage provider or is available through an external service, such as web site, MS Graph, etc.
    /// </summary>
    public MemoryRecordMetadata Metadata { get; }

    /// <summary>
    /// Search relevance, from 0 to 1, where 1 means perfect match.
    /// </summary>
    public double Relevance { get; }

    /// <summary>
    /// Nullable embedding associated with the metadata returned for by a query.
    /// </summary>
    public Embedding<float>? Embedding { get; }

    /// <summary>
    /// Create a new instance of MemoryQueryResult
    /// </summary>
    /// <param name="metadata">
    ///   Whether the source data used to calculate embeddings are stored in the local
    ///   storage provider or is available through an external service, such as web site, MS Graph, etc.
    /// </param>
    /// <param name="relevance">Search relevance, from 0 to 1, where 1 means perfect match.</param>
    /// <param name="embedding">Optional embedding associated with the metadata.</param>
    [JsonConstructor]
    public MemoryQueryResult(
        MemoryRecordMetadata metadata,
        double relevance,
        Embedding<float>? embedding)
    {
        this.Metadata = metadata;
        this.Relevance = relevance;
        this.Embedding = embedding;
    }

    /// <summary>
    /// Create MemoryQueryResult from a MemoryRecord
    /// </summary>
    /// <param name="rec">The memory record.</param>
    /// <param name="relevance">The search relevance score.</param>
    /// <param name="withEmbedding">Whether return the embedding from the memory record</param>
    /// <returns></returns>
    internal static MemoryQueryResult FromMemoryRecord(
        MemoryRecord rec,
        double relevance,
        bool withEmbedding = false)
    {
        return new MemoryQueryResult(
            (MemoryRecordMetadata)rec.Metadata.Clone(),
            relevance,
            (withEmbedding && !rec.Embedding.IsEmpty) ? rec.Embedding : null);
    }
}
