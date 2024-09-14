// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A description of a data property for storage in a memory store.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class MemoryRecordDataProperty : MemoryRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryRecordDataProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    public MemoryRecordDataProperty(string propertyName)
        : base(propertyName)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryRecordDataProperty"/> class by cloning the given source.
    /// </summary>
    /// <param name="source">The source to clone</param>
    public MemoryRecordDataProperty(MemoryRecordDataProperty source)
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
