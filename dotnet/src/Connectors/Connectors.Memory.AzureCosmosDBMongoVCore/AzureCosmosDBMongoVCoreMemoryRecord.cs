// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoVCore;

public sealed class AzureCosmosDBMongoVCoreMemoryRecord
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
    public AzureCosmosDBMongoVCoreMemoryRecordMetadata Metadata { get; set; }

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
    /// Initializes a new instance of the <see cref="AzureCosmosDBMongoVCoreMemoryRecord"/> class.
    /// </summary>
    /// <param name="memoryRecord"><see cref="MemoryRecord"/>Instance to copy values from.</param>
    public AzureCosmosDBMongoVCoreMemoryRecord(MemoryRecord memoryRecord)
    {
        this.Id = memoryRecord.Key;
        this.Metadata = new AzureCosmosDBMongoVCoreMemoryRecordMetadata(memoryRecord.Metadata);
        this.Embedding = memoryRecord.Embedding.ToArray();
        this.Timestamp = memoryRecord.Timestamp?.UtcDateTime;
    }

    /// <summary>
    /// Returns mapped <see cref="MemoryRecord"/>.
    /// </summary>
    public static MemoryRecord ToMemoryRecord(BsonDocument doc, bool withEmbedding) 
    {
        return new (
            BsonSerializer.Deserialize<AzureCosmosDBMongoVCoreMemoryRecordMetadata>(doc["metadata"].AsBsonDocument).ToMemoryRecordMetadata(),
            withEmbedding ? doc["embedding"].AsBsonArray.Select(x => (float)x.AsDouble).ToArray() : null,
            doc["_id"].AsString,
            doc["timestamp"]?.ToUniversalTime()
        );

        // return result;
    }

    /// <summary>
    /// Returns mapped <see cref="MemoryRecord"/>.
    /// </summary>
    public MemoryRecord ToMemoryRecord(bool withEmbedding)
    {
        return new(this.Metadata.ToMemoryRecordMetadata(), withEmbedding ? this.Embedding : null, this.Id, this.Timestamp?.ToLocalTime());
    }

}