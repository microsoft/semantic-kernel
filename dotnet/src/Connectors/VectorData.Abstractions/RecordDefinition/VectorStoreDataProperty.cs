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
    /// <param name="name">The name of the property on the data model. If the record is mapped to a .NET type, this corresponds to the .NET property name on that type.</param>
    /// <param name="type">The type of the property. Required when using a record type of <c>Dictionary&lt;string, object?&gt;</c> (dynamic mapping), but can be omitted when mapping any other .NET type.</param>
    public VectorStoreDataProperty(string name, Type? type = null)
        : base(name, type)
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
