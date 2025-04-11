// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// A MongoDB memory record.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureMongoDBMongoDBVectorStore")]
internal sealed class AzureCosmosDBMongoDBMemoryRecord
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
    public AzureCosmosDBMongoDBMemoryRecordMetadata Metadata { get; set; }

    /// <summary>
    /// Source content embedding.
    /// </summary>
#pragma warning disable CA1819 // Properties should not return arrays
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
    /// Initializes a new instance of the <see cref="AzureCosmosDBMongoDBMemoryRecord"/> class.
    /// </summary>
    /// <param name="memoryRecord"><see cref="MemoryRecord"/>Instance to copy values from.</param>
    public AzureCosmosDBMongoDBMemoryRecord(MemoryRecord memoryRecord)
    {
        this.Id = memoryRecord.Key;
        this.Metadata = new AzureCosmosDBMongoDBMemoryRecordMetadata(memoryRecord.Metadata);
        this.Embedding = memoryRecord.Embedding.ToArray();
        this.Timestamp = memoryRecord.Timestamp?.UtcDateTime;
    }

    /// <summary>
    /// Returns mapped <see cref="MemoryRecord"/>.
    /// </summary>
    public static MemoryRecord ToMemoryRecord(BsonDocument doc, bool withEmbedding)
    {
        BsonValue? timestamp = doc["timestamp"];
        DateTimeOffset? recordTimestamp = timestamp is BsonNull ? null : timestamp.ToUniversalTime();

        return new(
            BsonSerializer
                .Deserialize<AzureCosmosDBMongoDBMemoryRecordMetadata>(
                    doc["metadata"].AsBsonDocument
                )
                .ToMemoryRecordMetadata(),
            withEmbedding
                ? doc["embedding"].AsBsonArray.Select(x => (float)x.AsDouble).ToArray()
                : null,
            doc["_id"].AsString,
            recordTimestamp
        );
    }

    /// <summary>
    /// Returns mapped <see cref="MemoryRecord"/>.
    /// </summary>
    public MemoryRecord ToMemoryRecord(bool withEmbedding)
    {
        return new(
            this.Metadata.ToMemoryRecordMetadata(),
            withEmbedding ? this.Embedding : null,
            this.Id,
            this.Timestamp
        );
    }
}
