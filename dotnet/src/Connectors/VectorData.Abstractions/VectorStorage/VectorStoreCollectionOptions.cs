// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData;

/// <summary>Abstract base class for options passed to a collection..</summary>
public abstract class VectorStoreCollectionOptions
{
    /// <summary>
    /// An optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreKeyAttribute"/>, <see cref="VectorStoreDataAttribute"/> and <see cref="VectorStoreVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? Definition { get; set; }

    /// <summary>
    /// The default embedding generator to use when generating vectors embeddings with this collection.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
