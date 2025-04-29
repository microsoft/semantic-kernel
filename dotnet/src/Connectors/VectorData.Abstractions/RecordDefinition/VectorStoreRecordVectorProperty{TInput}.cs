// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a vector property on a vector store record.
/// </summary>
/// <remarks>
/// <para>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </para>
/// <para>
/// This generic version of <see cref="VectorStoreRecordVectorProperty"/> only needs to be used when an <see cref="IEmbeddingGenerator"/> is
/// configured on the property, and a custom .NET type is used as input (any type other than <see cref="string"/> or <see cref="DataContent"/>).
/// </para>
/// </remarks>
public class VectorStoreRecordVectorProperty<TInput> : VectorStoreRecordVectorProperty
{
    /// <inheritdoc />
    public VectorStoreRecordVectorProperty(string propertyName, int dimensions)
        : base(propertyName, typeof(TInput), dimensions)
    {
    }

    /// <inheritdoc />
    public VectorStoreRecordVectorProperty(VectorStoreRecordVectorProperty<TInput> source)
        : base(source)
    {
    }

    internal override VectorStoreRecordVectorPropertyModel CreatePropertyModel()
        => new VectorStoreRecordVectorPropertyModel<TInput>(this.DataModelPropertyName)
        {
            Dimensions = this.Dimensions,
            IndexKind = this.IndexKind,
            DistanceFunction = this.DistanceFunction,
            EmbeddingGenerator = this.EmbeddingGenerator
        };
}
