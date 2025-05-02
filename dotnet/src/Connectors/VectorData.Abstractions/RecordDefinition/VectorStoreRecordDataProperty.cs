// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a data property on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </remarks>
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
    /// <param name="source">The source to clone.</param>
    public VectorStoreRecordDataProperty(VectorStoreRecordDataProperty source)
        : base(source)
    {
        this.IsIndexed = source.IsIndexed;
        this.IsFullTextIndexed = source.IsFullTextIndexed;
    }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is filterable.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    [Obsolete("This property is now obsolete and will have no affect if used. Please use IsIndexed instead", error: true)]
    public bool IsFilterable { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is full text searchable.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    [Obsolete("This property is now obsolete and will have no affect if used. Please use IsFullTextIndexed instead", error: true)]
    public bool IsFullTextSearchable { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is indexed.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsIndexed { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is indexed for full-text search.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsFullTextIndexed { get; init; }
}
