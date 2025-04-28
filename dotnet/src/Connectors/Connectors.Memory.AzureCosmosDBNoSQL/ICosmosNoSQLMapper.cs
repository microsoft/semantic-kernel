// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

internal interface ICosmosNoSQLMapper<TRecord>
{
    /// <summary>
    /// Maps from the consumer record data model to the storage model.
    /// </summary>
    JsonObject MapFromDataToStorageModel(TRecord dataModel, MEAI.Embedding?[]? generatedEmbeddings);

    /// <summary>
    /// Maps from the storage model to the consumer record data model.
    /// </summary>
    TRecord MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options);
}
