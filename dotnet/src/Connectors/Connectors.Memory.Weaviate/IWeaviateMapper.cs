// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal interface IWeaviateMapper<TRecord>
{
    /// <summary>
    /// Maps from the consumer record data model to the storage model.
    /// </summary>
    JsonObject MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings);

    /// <summary>
    /// Maps from the storage model to the consumer record data model.
    /// </summary>
    TRecord MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options);
}
