// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal interface IWeaviateMapper<TRecord>
{
    /// <summary>
    /// Maps from the consumer record data model to the storage model.
    /// </summary>
    /// <param name="dataModel">The consumer record data model record to map.</param>
    /// <returns>The mapped result.</returns>
    JsonObject MapFromDataToStorageModel(TRecord dataModel);

    /// <summary>
    /// Maps from the storage model to the consumer record data model.
    /// </summary>
    /// <param name="storageModel">The storage data model record to map.</param>
    /// <param name="options">Options to control the mapping behavior.</param>
    /// <returns>The mapped result.</returns>
    TRecord MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options);
}
