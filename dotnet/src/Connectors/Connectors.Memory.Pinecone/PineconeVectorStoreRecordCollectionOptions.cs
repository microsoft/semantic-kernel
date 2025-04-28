// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Options when creating a <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class PineconeVectorStoreRecordCollectionOptions<TRecord>
{
    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and the Pinecone vector.
    /// </summary>
    [Obsolete("Custom mappers are no longer supported.", error: true)]
    public IVectorStoreRecordMapper<TRecord, Vector>? VectorCustomMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

    /// <summary>
    /// Gets or sets the value for a namespace within the Pinecone index that will be used for operations involving records (Get, Upsert, Delete)."/>
    /// </summary>
    public string? IndexNamespace { get; init; } = null;

    /// <summary>
    /// Gets or sets the value for public cloud where the serverless index is hosted.
    /// </summary>
    /// <remarks>
    /// This value is only used when creating a new Pinecone index. Default value is 'aws'.
    /// </remarks>
    public string ServerlessIndexCloud { get; init; } = "aws";

    /// <summary>
    /// Gets or sets the value for region where the serverless index is created.
    /// </summary>
    /// <remarks>
    /// This option is only used when creating a new Pinecone index. Default value is 'us-east-1'.
    /// </remarks>
    public string ServerlessIndexRegion { get; init; } = "us-east-1";

    /// <summary>
    /// Gets or sets the default embedding generator for vector properties in this collection.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
