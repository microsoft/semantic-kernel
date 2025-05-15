// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a data property on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </remarks>
public sealed class VectorStoreDataProperty : VectorStoreProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreDataProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    /// <param name="propertyType">The type of the property.</param>
    public VectorStoreDataProperty(string propertyName, Type propertyType)
        : base(propertyName, propertyType)
    {
    }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is indexed.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsIndexed { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is indexed for full-text search.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsFullTextIndexed { get; set; }
}
