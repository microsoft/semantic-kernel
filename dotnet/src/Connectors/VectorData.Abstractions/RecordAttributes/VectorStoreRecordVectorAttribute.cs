// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines an attribute to mark a property on a record class as a vector.
/// </summary>
/// <remarks>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </remarks>
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class VectorStoreRecordVectorAttribute : Attribute
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorAttribute"/> class.
    /// </summary>
    public VectorStoreRecordVectorAttribute()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorAttribute"/> class.
    /// </summary>
    /// <param name="Dimensions">The number of dimensions that the vector has.</param>
    public VectorStoreRecordVectorAttribute(int Dimensions)
    {
        this.Dimensions = Dimensions;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorAttribute"/> class.
    /// </summary>
    /// <param name="Dimensions">The number of dimensions that the vector has.</param>
    /// <param name="DistanceFunction">The distance function to use when comparing vectors.</param>
    public VectorStoreRecordVectorAttribute(int Dimensions, string? DistanceFunction)
    {
        this.Dimensions = Dimensions;
        this.DistanceFunction = DistanceFunction;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorAttribute"/> class.
    /// </summary>
    /// <param name="Dimensions">The number of dimensions that the vector has.</param>
    /// <param name="DistanceFunction">The distance function to use when comparing vectors.</param>
    /// <param name="IndexKind">The kind of index to use.</param>
    public VectorStoreRecordVectorAttribute(int Dimensions, string? DistanceFunction, string? IndexKind)
    {
        this.Dimensions = Dimensions;
        this.DistanceFunction = DistanceFunction;
        this.IndexKind = IndexKind;
    }

    /// <summary>
    /// Gets the number of dimensions that the vector has.
    /// </summary>
    /// <remarks>
    /// This property is required when creating collections, but can be omitted if not using that functionality.
    /// If not provided when trying to create a collection, create will fail.
    /// </remarks>
    public int? Dimensions { get; private set; }

    /// <summary>
    /// Gets the kind of index to use.
    /// </summary>
    /// <value>
    /// The default value varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="IndexKind"/>
    public string? IndexKind { get; private set; }

    /// <summary>
    /// Gets the distance function to use when comparing vectors.
    /// </summary>
    /// <value>
    /// The default value varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="DistanceFunction"/>
    public string? DistanceFunction { get; private set; }

    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// </summary>
    /// <remarks>
    /// For example, the property name might be "MyProperty" and the storage name might be "my_property".
    /// </remarks>
    public string? StoragePropertyName { get; set; }
}
