// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A description of a key property on a record for storage in a vector store.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VectorStoreRecordKeyProperty : VectorStoreRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordKeyProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    public VectorStoreRecordKeyProperty(string propertyName)
        : base(propertyName)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordKeyProperty"/> class by cloning the given source.
    /// </summary>
    /// <param name="source">The source to clone</param>
    public VectorStoreRecordKeyProperty(VectorStoreRecordKeyProperty source)
        : base(source.PropertyName)
    {
    }
}
