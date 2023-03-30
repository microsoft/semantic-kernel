// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;

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
    /// Create a new instance of MemoryQueryResult
    /// </summary>
    /// <param name="metadata">
    ///   Whether the source data used to calculate embeddings are stored in the local
    ///   storage provider or is available through an external service, such as web site, MS Graph, etc.
    /// </param>
    /// <param name="relevance">Search relevance, from 0 to 1, where 1 means perfect match.</param>
    [JsonConstructor]
    public MemoryQueryResult(
        MemoryRecordMetadata metadata,
        double relevance)
    {
        this.Metadata = metadata;
        this.Relevance = relevance;
    }

    public static MemoryQueryResult FromJson(
        string json,
        double relevance)
    {
        var metadata = JsonSerializer.Deserialize<MemoryRecordMetadata>(json);
        if (metadata != null)
        {
            return new MemoryQueryResult(metadata, relevance);
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
            relevance);
    }
}
