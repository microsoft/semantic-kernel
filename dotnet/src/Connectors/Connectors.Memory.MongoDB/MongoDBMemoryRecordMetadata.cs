// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// A MongoDB record metadata.
/// </summary>
#pragma warning disable CA1815 // Override equals and operator equals on value types
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and MongoDBVectorStore")]
public struct MongoDBMemoryRecordMetadata
#pragma warning restore CA1815 // Override equals and operator equals on value types
{
    /// <summary>
    /// <see cref="MemoryRecordMetadata.IsReference"/>.
    /// </summary>
    [BsonElement("isReference")]
    public bool IsReference { get; set; }

    /// <summary>
    /// <see cref="MemoryRecordMetadata.ExternalSourceName"/>.
    /// </summary>
    [BsonElement("externalSourceName")]
    [BsonIgnoreIfDefault]
    public string ExternalSourceName { get; set; }

    /// <summary>
    /// <see cref="MemoryRecordMetadata.Id"/>.
    /// </summary>
    [BsonId]
    public string Id { get; set; }

    /// <summary>
    /// <see cref="MemoryRecordMetadata.Description"/>.
    /// </summary>
    [BsonElement("description")]
    [BsonIgnoreIfDefault]
    public string Description { get; set; }

    /// <summary>
    /// <see cref="MemoryRecordMetadata.Text"/>.
    /// </summary>
    [BsonElement("text")]
    [BsonIgnoreIfDefault]
    public string Text { get; set; }

    /// <summary>
    /// <see cref="MemoryRecordMetadata.AdditionalMetadata"/>.
    /// </summary>
    [BsonElement("additionalMetadata")]
    [BsonIgnoreIfDefault]
    public string AdditionalMetadata { get; set; }

    /// <summary>
    /// Initializes a new instance of <see cref="MongoDBMemoryRecordMetadata"/> structure.
    /// </summary>
    public MongoDBMemoryRecordMetadata(MemoryRecordMetadata memoryRecordMetadata)
    {
        this.IsReference = memoryRecordMetadata.IsReference;
        this.ExternalSourceName = memoryRecordMetadata.ExternalSourceName;
        this.Id = memoryRecordMetadata.Id;
        this.Description = memoryRecordMetadata.Description;
        this.Text = memoryRecordMetadata.Text;
        this.AdditionalMetadata = memoryRecordMetadata.AdditionalMetadata;
    }

    /// <summary>
    /// Returns mapped <see cref="MemoryRecordMetadata"/>.
    /// </summary>
    public MemoryRecordMetadata ToMemoryRecordMetadata() =>
        new(this.IsReference, this.Id, this.Text, this.Description, this.ExternalSourceName, this.AdditionalMetadata);
}
