// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Options when creating a <see cref="PineconeVectorStoreRecordCollection{TRecord}"/>.
/// </summary>
public sealed class PineconeVectorStoreRecordCollectionOptions<TRecord>
    where TRecord : class
{
    /// <summary>
    /// Gets or sets the choice of mapper to use when converting between the data model and the Pinecone vector.
    /// </summary>
    public PineconeRecordMapperType MapperType { get; init; } = PineconeRecordMapperType.Default;

    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and the Pinecone vector.
    /// </summary>
    /// <remarks>
    /// Set <see cref="MapperType"/> to <see cref="PineconeRecordMapperType.PineconeVectorCustomMapper"/> to use this mapper."/>
    /// </remarks>
    public IVectorStoreRecordMapper<TRecord, Vector>? VectorCustomMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;
}
