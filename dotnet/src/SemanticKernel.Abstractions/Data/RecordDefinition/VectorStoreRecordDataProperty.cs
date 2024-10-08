// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Defines a data property on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here will influence how the property is treated by the vector store.
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class VectorStoreRecordDataProperty : VectorStoreRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordDataProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    /// <param name="propertyType">The type of the property.</param>
    public VectorStoreRecordDataProperty(string propertyName, Type propertyType)
        : base(propertyName, propertyType)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordDataProperty"/> class by cloning the given source.
    /// </summary>
    /// <param name="source">The source to clone</param>
    public VectorStoreRecordDataProperty(VectorStoreRecordDataProperty source)
        : base(source)
    {
        this.IsFilterable = source.IsFilterable;
        this.IsFullTextSearchable = source.IsFullTextSearchable;
    }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is filterable.
    /// </summary>
    /// <remarks>
    /// Default is <see langword="false" />.
    /// </remarks>
    public bool IsFilterable { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is full text searchable.
    /// </summary>
    /// <remarks>
    /// Default is <see langword="false" />.
    /// </remarks>
    public bool IsFullTextSearchable { get; init; }
}
