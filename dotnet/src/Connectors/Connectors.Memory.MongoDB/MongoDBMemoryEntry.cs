// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.Memory.MongoDB;

/// <summary>
/// A MongoDB memory entry.
/// </summary>
public sealed class MongoDBMemoryEntry
{
    /// <summary>
    /// Unique identifier of the memory entry.
    /// </summary>
    public string Id { get; set; }

    /// <summary>
    /// Metadata associated with memory entity.
    /// </summary>
    [BsonIgnoreIfDefault]
    public MemoryRecordMetadata Metadata { get; set; }

    /// <summary>
    /// Source content embedding.
    /// </summary>
#pragma warning disable CA1819 // Properties should not return arrays
    public float[] Embedding { get; set; }
#pragma warning restore CA1819 // Properties should not return arrays

    /// <summary>
    /// Optional timestamp.
    /// </summary>
    public DateTimeOffset? Timestamp { get; set; }

    /// <summary>
    /// Nearest match score.
    /// </summary>
    [BsonIgnoreIfDefault]
    public double Score { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBMemoryEntry"/> class.
    /// </summary>
    /// <param name="memoryRecord"><see cref="MemoryRecord"/>Instance to copy values from.</param>
    public MongoDBMemoryEntry(MemoryRecord memoryRecord)
    {
        this.Id = memoryRecord.Key;
        this.Metadata = memoryRecord.Metadata; // Metadata is readonly
        this.Embedding = memoryRecord.Embedding.ToArray();
        this.Timestamp = memoryRecord.Timestamp;
    }

    /// <summary>
    /// Returns mapped <see cref="MemoryRecord"/>.
    /// </summary>
    public MemoryRecord ToMemoryRecord() =>
        new(this.Metadata, this.Embedding, this.Id, this.Timestamp);

    /// <summary>
    /// Returns a pair of mapped <see cref="MemoryRecord"/> and score.
    /// </summary>
    public (MemoryRecord, double) ToMemoryRecordAndScore() =>
        (new(this.Metadata, this.Embedding, this.Id, this.Timestamp), this.Score);
}
