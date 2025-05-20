// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a vector property on a vector store record.
/// </summary>
/// <remarks>
/// <para>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </para>
/// <para>
/// This generic version of <see cref="VectorStoreVectorProperty"/> only needs to be used when an <see cref="IEmbeddingGenerator"/> is
/// configured on the property, and a custom .NET type is used as input (any type other than <see cref="string"/> or <see cref="DataContent"/>).
/// </para>
/// </remarks>
public class VectorStoreVectorProperty<TInput> : VectorStoreVectorProperty
{
    /// <inheritdoc />
    public VectorStoreVectorProperty(string propertyName, int dimensions)
        : base(propertyName, typeof(TInput), dimensions)
    {
    }

    internal override VectorPropertyModel CreatePropertyModel()
        => new VectorPropertyModel<TInput>(this.Name)
        {
            Dimensions = this.Dimensions,
            IndexKind = this.IndexKind,
            DistanceFunction = this.DistanceFunction,
            EmbeddingGenerator = this.EmbeddingGenerator
        };
}
