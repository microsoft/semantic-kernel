// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A description of a vector property on a record for storage in a vector store.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VectorStoreRecordVectorProperty : VectorStoreRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    public VectorStoreRecordVectorProperty(string propertyName)
        : base(propertyName)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorProperty"/> class by cloning the given source.
    /// </summary>
    /// <param name="source">The source to clone</param>
    public VectorStoreRecordVectorProperty(VectorStoreRecordVectorProperty source)
        : base(source.PropertyName)
    {
    }
}
