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
public sealed class VectorStoreVectorAttribute : Attribute
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreVectorAttribute"/> class.
    /// </summary>
    /// <param name="Dimensions">The number of dimensions that the vector has.</param>
    public VectorStoreVectorAttribute(int Dimensions)
    {
        if (Dimensions <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(Dimensions), "Dimensions must be greater than zero.");
        }

        this.Dimensions = Dimensions;
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
    /// Gets or sets the kind of index to use.
    /// </summary>
    /// <value>
    /// The default value varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="IndexKind"/>
#pragma warning disable CA1019 // Define accessors for attribute arguments: The constructor overload that contains this property is obsolete.
    public string? IndexKind { get; init; }
#pragma warning restore CA1019

    /// <summary>
    /// Gets or sets the distance function to use when comparing vectors.
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
    public string? StorageName { get; init; }
}
