// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCosmosDBMongoVCore;

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
    // AzureCosmosDBMongoVCoreMemoryRecord class is not part of public API, and its usage correctness is ensured by AzureCosmosDBMongoVCoreStore.
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
    public MemoryRecord ToMemoryRecord(bool withEmbedding) =>
        MemoryRecord result = new()
        {
            Metadata = this.Metadata.ToMemoryRecordMetadata();
            Key = this.Id;
            Timestamp = this.Timestamp?.ToLocalTime()
        }    

        if (withEmbedding)
        {
            result.Embedding = this.Embedding;
        }
        return result;

}