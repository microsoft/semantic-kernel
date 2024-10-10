// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Defines a vector property on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here will influence how the property is treated by the vector store.
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class VectorStoreRecordVectorProperty : VectorStoreRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    /// <param name="propertyType">The type of the property.</param>
    public VectorStoreRecordVectorProperty(string propertyName, Type propertyType)
        : base(propertyName, propertyType)
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
    /// <remarks>
    /// This property is required when creating collections, but may be omitted if not using that functionality.
    /// If not provided when trying to create a collection, create will fail.
    /// </remarks>
    public int? Dimensions { get; init; }

    /// <summary>
    /// Gets the kind of index to use.
    /// </summary>
    /// <seealso cref="IndexKind"/>
    /// <remarks>
    /// Default varies by database type. See the documentation of your chosen database connector for more information.
    /// </remarks>
    public string? IndexKind { get; init; }

    /// <summary>
    /// Gets the distance function to use when comparing vectors.
    /// </summary>
    /// <seealso cref="DistanceFunction"/>
    /// <remarks>
    /// Default varies by database type. See the documentation of your chosen database connector for more information.
    /// </remarks>
    public string? DistanceFunction { get; init; }
}
