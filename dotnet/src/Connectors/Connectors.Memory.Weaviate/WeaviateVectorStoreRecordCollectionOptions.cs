// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Options when creating a <see cref="WeaviateVectorStoreRecordCollection{TRecord}"/>.
/// </summary>
public sealed class WeaviateVectorStoreRecordCollectionOptions<TRecord> where TRecord : class
{
    public IVectorStoreRecordMapper<TRecord, JsonNode>? JsonNodeCustomMapper { get; set; } = null;

    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;
}
