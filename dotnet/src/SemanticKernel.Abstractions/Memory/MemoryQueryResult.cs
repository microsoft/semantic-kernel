// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

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
    [JsonConverter(typeof(ReadOnlyMemoryConverter))]
    public ReadOnlyMemory<float>? Embedding { get; }

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
        ReadOnlyMemory<float>? embedding)
    {
        this.Metadata = metadata;
        this.Relevance = relevance;
        this.Embedding = embedding;
    }

    /// <summary>
    /// Creates instance of <see cref="MemoryQueryResult"/> based on <see cref="MemoryRecord"/> and search relevance.
    /// </summary>
    /// <param name="record">Instance of <see cref="MemoryRecord"/>.</param>
    /// <param name="relevance">Search relevance, from 0 to 1, where 1 means perfect match.</param>
    public static MemoryQueryResult FromMemoryRecord(
        MemoryRecord record,
        double relevance)
    {
        return new MemoryQueryResult(
            (MemoryRecordMetadata)record.Metadata.Clone(),
            relevance,
            record.Embedding.IsEmpty ? null : record.Embedding);
    }
}
