// Copyright (c) Microsoft. All rights reserved.

using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// The types of mapper supported by <see cref="QdrantVectorRecordStore{TRecord}"/>.
/// </summary>
public enum QdrantRecordMapperType
{
    /// <summary>
    /// Use the default mapper that is provided by the semantic kernel SDK that uses json as an intermediary to allows automatic mapping to a wide variety of types.
    /// </summary>
    Default,

    /// <summary>
    /// Use a custom mapper between <see cref="PointStruct"/> and the data model.
    /// </summary>
    QdrantPointStructCustomMapper
}
