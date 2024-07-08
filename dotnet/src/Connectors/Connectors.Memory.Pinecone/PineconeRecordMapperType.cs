// Copyright (c) Microsoft. All rights reserved.

using Sdk = Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// The types of mapper supported by <see cref="PineconeVectorStoreRecordCollection{TRecord}"/>.
/// </summary>
public enum PineconeRecordMapperType
{
    /// <summary>
    /// Use the default mapper that is provided by the semantic kernel SDK that uses json as an intermediary to allows automatic mapping to a wide variety of types.
    /// </summary>
    Default,

    /// <summary>
    /// Use a custom mapper between <see cref="Sdk.Vector"/> and the data model.
    /// </summary>
    PineconeVectorCustomMapper
}
