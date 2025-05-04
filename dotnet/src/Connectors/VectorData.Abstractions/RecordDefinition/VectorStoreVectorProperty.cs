// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a vector property on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </remarks>
public class VectorStoreVectorProperty : VectorStoreProperty
{
    private int _dimensions;

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreVectorProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    /// <param name="propertyType">The type of the property.</param>
    [Obsolete("This constructor is obsolete, since dimensions is now a required parameter.", error: true)]
    public VectorStoreVectorProperty(string propertyName, Type propertyType)
        : base(propertyName, propertyType)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreVectorProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    /// <param name="propertyType">The type of the property.</param>
    /// <param name="dimensions">The number of dimensions that the vector has.</param>
    public VectorStoreVectorProperty(string propertyName, Type propertyType, int dimensions)
        : base(propertyName, propertyType)
    {
        this.Dimensions = dimensions;
    }

    /// <summary>
    /// Gets or sets the default embedding generator to use for this property.
    /// </summary>
    /// <remarks>
    /// If not set, embedding generation will be performed in the database, if supported by your connector.
    /// If not supported, only pre-generated embeddings can be used, e.g. via <see cref="IVectorSearchable{TRecord}.SearchEmbeddingAsync{TVector}"/>.
    /// </remarks>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }

    /// <summary>
    /// Gets or sets the number of dimensions that the vector has.
    /// </summary>
    /// <remarks>
    /// This property is required when creating collections, but can be omitted if not using that functionality.
    /// If not provided when trying to create a collection, create will fail.
    /// </remarks>
    public int Dimensions
    {
        get => this._dimensions;

        set
        {
            if (value <= 0)
            {
                throw new ArgumentOutOfRangeException(nameof(value), "Dimensions must be greater than zero.");
            }

            this._dimensions = value;
        }
    }

    /// <summary>
    /// Gets or sets the kind of index to use.
    /// </summary>
    /// <value>
    /// The default varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="Microsoft.Extensions.VectorData.IndexKind"/>
    public string? IndexKind { get; set; }

    /// <summary>
    /// Gets or sets the distance function to use when comparing vectors.
    /// </summary>
    /// <value>
    /// The default varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="Microsoft.Extensions.VectorData.DistanceFunction"/>
    public string? DistanceFunction { get; set; }

    /// <summary>
    /// Gets or sets the desired embedding type (e.g. <c>Embedding&lt;Half&gt;</c>, for cases where the default (typically <c>Embedding&lt;float&gt;</c>) isn't suitable.
    /// </summary>
    public Type? EmbeddingType { get; set; }

    internal virtual VectorPropertyModel CreatePropertyModel()
        => new(this.DataModelPropertyName, this.PropertyType)
        {
            Dimensions = this.Dimensions,
            IndexKind = this.IndexKind,
            DistanceFunction = this.DistanceFunction,
            EmbeddingGenerator = this.EmbeddingGenerator,
            EmbeddingType = this.EmbeddingType!
        };
}
