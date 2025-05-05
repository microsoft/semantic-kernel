// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a key property on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </remarks>
public sealed class VectorStoreKeyProperty : VectorStoreProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreKeyProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    /// <param name="propertyType">The type of the property.</param>
    public VectorStoreKeyProperty(string propertyName, Type propertyType)
        : base(propertyName, propertyType)
    {
    }
}
