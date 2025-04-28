// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Options when creating a <see cref="MongoDBVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class MongoDBVectorStoreRecordCollectionOptions<TRecord>
{
    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and the MongoDB BSON object.
    /// </summary>
    [Obsolete("Custom mappers are no longer supported.", error: true)]
    public IVectorStoreRecordMapper<TRecord, BsonDocument>? BsonDocumentCustomMapper { get; init; } = null;

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
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }

    /// <summary>
    /// Vector index name to use. If null, the default "vector_index" name will be used.
    /// </summary>
    public string VectorIndexName { get; init; } = MongoDBConstants.DefaultVectorIndexName;

    /// <summary>
    /// Full text search index name to use. If null, the default "full_text_search_index" name will be used.
    /// </summary>
    public string FullTextSearchIndexName { get; init; } = MongoDBConstants.DefaultFullTextSearchIndexName;

    /// <summary>
    /// Number of max retries for vector collection operation.
    /// </summary>
    public int MaxRetries { get; init; } = 5;

    /// <summary>
    /// Delay in milliseconds between retries for vector collection operation.
    /// </summary>
    public int DelayInMilliseconds { get; init; } = 1_000;

    /// <summary>
    /// Number of nearest neighbors to use during the vector search.
    /// Value must be less than or equal to 10000.
    /// Recommended value should be higher than number of documents to return.
    /// If not provided, "number of documents * 10" value will be used.
    /// </summary>
    public int? NumCandidates { get; init; } = null;
}
