// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Defines a key property on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here will influence how the property is treated by the vector store.
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class VectorStoreRecordKeyProperty : VectorStoreRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordKeyProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    /// <param name="propertyType">The type of the property.</param>
    public VectorStoreRecordKeyProperty(string propertyName, Type propertyType)
        : base(propertyName, propertyType)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordKeyProperty"/> class by cloning the given source.
    /// </summary>
    /// <param name="source">The source to clone</param>
    public VectorStoreRecordKeyProperty(VectorStoreRecordKeyProperty source)
        : base(source)
    {
    }
}
