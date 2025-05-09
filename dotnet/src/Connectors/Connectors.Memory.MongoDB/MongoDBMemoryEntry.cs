// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// A MongoDB memory entry.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and MongoDBVectorStore")]
public sealed class MongoDBMemoryEntry
{
    /// <summary>
    /// Unique identifier of the memory entry.
    /// </summary>
    [BsonId]
    public string Id { get; set; }

    /// <summary>
    /// Metadata associated with memory entity.
    /// </summary>
    [BsonElement("metadata")]
    public MongoDBMemoryRecordMetadata Metadata { get; set; }

    /// <summary>
    /// Source content embedding.
    /// </summary>
#pragma warning disable CA1819 // Properties should not return arrays
    // MongoDBMemoryEntry class is not part of public API, and its usage correctness is ensured by MongoDBMemoryStore.
    // This is an interim solution until ReadOnlyMemory<T> serialization is supported natively by MongoDB Driver (https://jira.mongodb.org/browse/CSHARP-4807).
    [BsonElement("embedding")]
    public float[] Embedding { get; set; }
#pragma warning restore CA1819 // Properties should not return arrays

    /// <summary>
    /// Optional timestamp.
    /// </summary>
    [BsonElement("timestamp")]
    [BsonDateTimeOptions(Kind = DateTimeKind.Utc, Representation = BsonType.DateTime)]
    public DateTime? Timestamp { get; set; }

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
        this.Metadata = new MongoDBMemoryRecordMetadata(memoryRecord.Metadata);
        this.Embedding = memoryRecord.Embedding.ToArray();
        this.Timestamp = memoryRecord.Timestamp?.UtcDateTime;
    }

    /// <summary>
    /// Returns mapped <see cref="MemoryRecord"/>.
    /// </summary>
    public MemoryRecord ToMemoryRecord() =>
        new(this.Metadata.ToMemoryRecordMetadata(), this.Embedding, this.Id, this.Timestamp?.ToLocalTime());

    /// <summary>
    /// Returns a pair of mapped <see cref="MemoryRecord"/> and score.
    /// </summary>
    public (MemoryRecord, double) ToMemoryRecordAndScore() =>
        (new(this.Metadata.ToMemoryRecordMetadata(), this.Embedding, this.Id, this.Timestamp?.ToLocalTime()), this.Score);
}
