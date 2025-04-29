// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Options when creating a <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/>.
/// </summary>
/// <typeparam name="TKey">The data type of the record key of the collection that this options will be used with.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data on the collection that this options will be used with.</typeparam>
public sealed class InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>
    where TKey : notnull
{
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
    /// An optional function that can be used to look up vectors from a record.
    /// </summary>
    /// <remarks>
    /// If not provided, the default behavior is to look for direct properties of the record
    /// using reflection. This delegate can be used to provide a custom implementation if
    /// the vector properties are located somewhere else on the record.
    /// </remarks>
    [Experimental("MEVD9000")]
    public InMemoryVectorStoreVectorResolver<TRecord>? VectorResolver { get; init; } = null;

    /// <summary>
    /// An optional function that can be used to look up record keys.
    /// </summary>
    /// <remarks>
    /// If not provided, the default behavior is to look for a direct property of the record
    /// using reflection. This delegate can be used to provide a custom implementation if
    /// the key property is located somewhere else on the record.
    /// </remarks>
    [Experimental("MEVD9000")]
    public InMemoryVectorStoreKeyResolver<TKey, TRecord>? KeyResolver { get; init; } = null;
}
