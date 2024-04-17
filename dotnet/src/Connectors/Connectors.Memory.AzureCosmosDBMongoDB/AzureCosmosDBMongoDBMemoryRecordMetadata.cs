// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// A MongoDB memory record metadata.
/// </summary>
#pragma warning disable CA1815 // Override equals and operator equals on value types
public struct AzureCosmosDBMongoDBMemoryRecordMetadata
#pragma warning restore CA1815 // Override equals and operator equals on value types
{
    /// <summary>
    /// <see cref="AzureCosmosDBMongoDBMemoryRecordMetadata.IsReference"/>.
    /// </summary>
    [BsonElement("isReference")]
    public bool IsReference { get; set; }

    /// <summary>
    /// <see cref="AzureCosmosDBMongoDBMemoryRecordMetadata.ExternalSourceName"/>.
    /// </summary>
    [BsonElement("externalSourceName")]
    [BsonIgnoreIfDefault]
    public string ExternalSourceName { get; set; }

    /// <summary>
    /// <see cref="AzureCosmosDBMongoDBMemoryRecordMetadata.Id"/>.
    /// </summary>
    [BsonId]
    public string Id { get; set; }

    /// <summary>
    /// <see cref="AzureCosmosDBMongoDBMemoryRecordMetadata.Description"/>.
    /// </summary>
    [BsonElement("description")]
    [BsonIgnoreIfDefault]
    public string Description { get; set; }

    /// <summary>
    /// <see cref="AzureCosmosDBMongoDBMemoryRecordMetadata.Text"/>.
    /// </summary>
    [BsonElement("text")]
    [BsonIgnoreIfDefault]
    public string Text { get; set; }

    /// <summary>
    /// <see cref="AzureCosmosDBMongoDBMemoryRecordMetadata.AdditionalMetadata"/>.
    /// </summary>
    [BsonElement("additionalMetadata")]
    [BsonIgnoreIfDefault]
    public string AdditionalMetadata { get; set; }

    /// <summary>
    /// Initializes a new instance of <see cref="AzureCosmosDBMongoDBMemoryRecordMetadata"/> structure.
    /// </summary>
    public AzureCosmosDBMongoDBMemoryRecordMetadata(MemoryRecordMetadata memoryRecordMetadata)
    {
        this.IsReference = memoryRecordMetadata.IsReference;
        this.ExternalSourceName = memoryRecordMetadata.ExternalSourceName;
        this.Id = memoryRecordMetadata.Id;
        this.Description = memoryRecordMetadata.Description;
        this.Text = memoryRecordMetadata.Text;
        this.AdditionalMetadata = memoryRecordMetadata.AdditionalMetadata;
    }

    /// <summary>
    /// Returns mapped <see cref="AzureCosmosDBMongoDBMemoryRecordMetadata"/>.
    /// </summary>
    public MemoryRecordMetadata ToMemoryRecordMetadata() =>
        new(
            this.IsReference,
            this.ExternalSourceName,
            this.Id,
            this.Description,
            this.Text,
            this.AdditionalMetadata
        );
}
