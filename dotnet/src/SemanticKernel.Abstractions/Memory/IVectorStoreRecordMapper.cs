// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Interface for mapping between a storage model, and the consumer record data model.
/// </summary>
/// <typeparam name="TRecordDataModel">The consumer record data model to map to or from.</typeparam>
/// <typeparam name="TStorageModel">The storage model to map to or from.</typeparam>
public interface IVectorStoreRecordMapper<TRecordDataModel, TStorageModel>
    where TRecordDataModel : class
{
    /// <summary>
    /// Map from the consumer record data model to the storage model.
    /// </summary>
    /// <param name="dataModel">The consumer record data model record to map.</param>
    /// <returns>The mapped result.</returns>
    TStorageModel MapFromDataToStorageModel(TRecordDataModel dataModel);

    /// <summary>
    /// Map from the storage model to the consumer record data model.
    /// </summary>
    /// <param name="storageModel">The storage data model record to map.</param>
    /// <param name="options">The <see cref="GetRecordOptions"/> of the operation that this mapping is needed for.</param>
    /// <returns>The mapped result.</returns>
    TRecordDataModel MapFromStorageToDataModel(TStorageModel storageModel, GetRecordOptions? options = default);
}
