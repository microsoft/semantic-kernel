// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines an interface for mapping between a storage model and the consumer record data model.
/// </summary>
/// <typeparam name="TRecordDataModel">The consumer record data model to map to or from.</typeparam>
/// <typeparam name="TStorageModel">The storage model to map to or from.</typeparam>
[Obsolete("Custom mappers are no longer supported.", error: true)]
public interface IVectorStoreRecordMapper<TRecordDataModel, TStorageModel>
{
    /// <summary>
    /// Maps from the consumer record data model to the storage model.
    /// </summary>
    /// <param name="dataModel">The consumer record data model record to map.</param>
    /// <returns>The mapped result.</returns>
    TStorageModel MapFromDataToStorageModel(TRecordDataModel dataModel);

    /// <summary>
    /// Maps from the storage model to the consumer record data model.
    /// </summary>
    /// <param name="storageModel">The storage data model record to map.</param>
    /// <param name="options">Options to control the mapping behavior.</param>
    /// <returns>The mapped result.</returns>
    TRecordDataModel MapFromStorageToDataModel(TStorageModel storageModel, StorageToDataModelMapperOptions options);
}
