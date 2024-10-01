// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Class for mapping between a dictionary and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class SqliteVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>>
    where TRecord : class
{
    public Dictionary<string, object?> MapFromDataToStorageModel(TRecord dataModel)
    {
        throw new System.NotImplementedException();
    }

    public TRecord MapFromStorageToDataModel(Dictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        throw new System.NotImplementedException();
    }
}
