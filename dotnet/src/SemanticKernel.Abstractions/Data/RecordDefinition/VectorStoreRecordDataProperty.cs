// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A description of a data property on a record for storage in a vector store.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VectorStoreRecordDataProperty : VectorStoreRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordDataProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    public VectorStoreRecordDataProperty(string propertyName)
        : base(propertyName)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordDataProperty"/> class by cloning the given source.
    /// </summary>
    /// <param name="source">The source to clone</param>
    public VectorStoreRecordDataProperty(VectorStoreRecordDataProperty source)
        : base(source.PropertyName)
    {
        this.HasEmbedding = source.HasEmbedding;
        this.EmbeddingPropertyName = source.EmbeddingPropertyName;
    }

    /// <summary>
    /// Gets or sets a value indicating whether this data property has an associated embedding property.
    /// </summary>
    /// <remarks>Defaults to <see langword="false" /></remarks>
    public bool HasEmbedding { get; init; }

    /// <summary>
    /// Gets or sets the name of the property that contains the embedding for this data property.
    /// </summary>
    public string? EmbeddingPropertyName { get; init; }
}
