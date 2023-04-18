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
    /// Create a new instance of MemoryQueryResult from a json string representing MemoryRecord metadata.
    /// </summary>
    /// <param name="json">The json string to deserialize.</param>
    /// <param name="relevance">The similarity score associated with the result.</param>
    /// <param name="embedding">Optional embedding associated with the metadata.</param>
    /// <returns>A new instance of MemoryQueryResult.</returns>
    /// <exception cref="MemoryException"></exception>
    public static MemoryQueryResult FromJsonMetadata(
        string json,
        double relevance,
        Embedding<float> embedding)
    {
        var metadata = JsonSerializer.Deserialize<MemoryRecordMetadata>(json);
        if (metadata != null)
        {
            return new MemoryQueryResult(metadata, relevance, embedding.IsEmpty ? null : embedding);
        }
        else
        {
            throw new MemoryException(
                MemoryException.ErrorCodes.UnableToDeserializeMetadata,
                "Unable to create memory query result from serialized metadata");
        }
    }

    internal static MemoryQueryResult FromMemoryRecord(
        MemoryRecord rec,
        double relevance)
    {
        return new MemoryQueryResult(
            (MemoryRecordMetadata)rec.Metadata.Clone(),
            relevance,
            rec.Embedding.IsEmpty ? null : rec.Embedding);
    }
}
