// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData;

/// <summary>Defines an abstract base class for options passed to a collection.</summary>
public abstract class VectorStoreCollectionOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreCollectionOptions"/> class.
    /// </summary>
    protected VectorStoreCollectionOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreCollectionOptions"/> class.
    /// </summary>
    protected VectorStoreCollectionOptions(VectorStoreCollectionOptions? source)
    {
        this.Definition = source?.Definition;
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreKeyAttribute"/>, <see cref="VectorStoreDataAttribute"/>, and <see cref="VectorStoreVectorAttribute"/>.
    /// </remarks>
    public VectorStoreCollectionDefinition? Definition { get; set; }

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this collection.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
