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
    [Obsolete("This constructor is obsolete, since Dimensions is now a required parameter.", error: true)]
    public VectorStoreRecordVectorAttribute()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorAttribute"/> class.
    /// </summary>
    /// <param name="Dimensions">The number of dimensions that the vector has.</param>
    public VectorStoreRecordVectorAttribute(int Dimensions)
    {
        if (Dimensions <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(Dimensions), "Dimensions must be greater than zero.");
        }

        this.Dimensions = Dimensions;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordVectorAttribute"/> class.
    /// </summary>
    /// <param name="Dimensions">The number of dimensions that the vector has.</param>
    /// <param name="DistanceFunction">The distance function to use when comparing vectors.</param>
    [Obsolete("This constructor is obsolete. Use the constructor that takes Dimensions as a parameter and set the DistanceFunction property directly, e.g. [[VectorStoreRecordVector(Dimensions: 1536, DistanceFunction = DistanceFunction.CosineSimilarity)]]", error: true)]
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
    [Obsolete("This constructor is obsolete. Use the constructor that takes Dimensions as a parameter and set the DistanceFunction and IndexKind properties directly, e.g. [[VectorStoreRecordVector(Dimensions: 1536, DistanceFunction = DistanceFunction.CosineSimilarity, IndexKind = IndexKind.Flat)]]", error: true)]
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
    public int Dimensions { get; private set; }

    /// <summary>
    /// Gets the kind of index to use.
    /// </summary>
    /// <value>
    /// The default value varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="IndexKind"/>
#pragma warning disable CA1019 // Define accessors for attribute arguments: The constructor overload that contains this property is obsolete.
    public string? IndexKind { get; init; }
#pragma warning restore CA1019

    /// <summary>
    /// Gets the distance function to use when comparing vectors.
    /// </summary>
    /// <value>
    /// The default value varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="DistanceFunction"/>
#pragma warning disable CA1019 // Define accessors for attribute arguments: The constructor overload that contains this property is obsolete.
    public string? DistanceFunction { get; init; }
#pragma warning restore CA1019

    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// </summary>
    /// <remarks>
    /// For example, the property name might be "MyProperty" and the storage name might be "my_property".
    /// </remarks>
    public string? StoragePropertyName { get; init; }
}
