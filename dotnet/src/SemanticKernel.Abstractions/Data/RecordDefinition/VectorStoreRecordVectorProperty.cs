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
        : base(source)
    {
        this.Dimensions = source.Dimensions;
        this.IndexKind = source.IndexKind;
        this.DistanceFunction = source.DistanceFunction;
    }

    /// <summary>
    /// Gets or sets the number of dimensions that the vector has.
    /// </summary>
    public int? Dimensions { get; init; }

    /// <summary>
    /// Gets the kind of index to use.
    /// </summary>
    /// <seealso cref="IndexKind"/>
    public string? IndexKind { get; init; }

    /// <summary>
    /// Gets the distance function to use when comparing vectors.
    /// </summary>
    /// <seealso cref="DistanceFunction"/>
    public string? DistanceFunction { get; init; }
}
