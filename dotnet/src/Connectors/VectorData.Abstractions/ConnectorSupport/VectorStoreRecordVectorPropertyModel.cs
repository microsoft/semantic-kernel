// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// Represents a vector property on a vector store record.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
[Experimental("MEVD9001")]
public class VectorStoreRecordVectorPropertyModel(string modelName, Type type) : VectorStoreRecordPropertyModel(modelName, type)
{
    /// <summary>
    /// The number of dimensions that the vector has.
    /// </summary>
    /// <remarks>
    /// This property is required when creating collections, but can be omitted if not using that functionality.
    /// If not provided when trying to create a collection, create will fail.
    /// </remarks>
    public int? Dimensions { get; set; }

    /// <summary>
    /// The kind of index to use.
    /// </summary>
    /// <value>
    /// The default varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="Microsoft.Extensions.VectorData.IndexKind"/>
    public string? IndexKind { get; set; }

    /// <summary>
    /// The distance function to use when comparing vectors.
    /// </summary>
    /// <value>
    /// The default varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="Microsoft.Extensions.VectorData.DistanceFunction"/>
    public string? DistanceFunction { get; set; }

    /// <inheritdoc/>
    public override string ToString()
        => $"{this.ModelName} (Vector, {this.Type.Name})";
}
