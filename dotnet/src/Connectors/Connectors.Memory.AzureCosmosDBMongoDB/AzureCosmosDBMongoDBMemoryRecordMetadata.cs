// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// A MongoDB memory record metadata.
/// </summary>
#pragma warning disable CA1815 // Override equals and operator equals on value types
[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureMongoDBMongoDBVectorStore")]
internal struct AzureCosmosDBMongoDBMemoryRecordMetadata
#pragma warning restore CA1815 // Override equals and operator equals on value types
{
    /// <summary>
    /// Whether the source data used to calculate embeddings are stored in the local
    /// storage provider or is available through and external service, such as web site, MS Graph, etc.
    /// </summary>
    [BsonElement("isReference")]
    public bool IsReference { get; set; }

    /// <summary>
    /// A value used to understand which external service owns the data, to avoid storing the information
    /// inside the URI. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.
    /// </summary>
    [BsonElement("externalSourceName")]
    [BsonIgnoreIfDefault]
    public string ExternalSourceName { get; set; }

    /// <summary>
    /// Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID, etc.
    /// </summary>
    [BsonId]
    public string Id { get; set; }

    /// <summary>
    /// Optional title describing the content. Note: the title is not indexed.
    /// </summary>
    [BsonElement("description")]
    [BsonIgnoreIfDefault]
    public string Description { get; set; }

    /// <summary>
    /// Source text, available only when the memory is not an external source.
    /// </summary>
    [BsonElement("text")]
    [BsonIgnoreIfDefault]
    public string Text { get; set; }

    /// <summary>
    /// Field for saving custom metadata with a memory.
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
            this.Id,
            this.Text,
            this.Description,
            this.ExternalSourceName,
            this.AdditionalMetadata
        );
}
