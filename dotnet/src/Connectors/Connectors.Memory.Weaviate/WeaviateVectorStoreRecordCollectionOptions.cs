// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Options when creating a <see cref="WeaviateVectorStoreRecordCollection{TRecord}"/>.
/// </summary>
public sealed class WeaviateVectorStoreRecordCollectionOptions<TRecord> where TRecord : class
{
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

    public JsonSerializerOptions? JsonSerializerOptions { get; init; } = null;
}
