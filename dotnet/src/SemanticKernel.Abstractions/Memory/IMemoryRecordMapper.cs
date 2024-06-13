// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Interface for mapping between a storage model, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
/// <typeparam name="TStorageModel">The storage model to map to or from.</typeparam>
public interface IMemoryRecordMapper<TConsumerDataModel, TStorageModel>
    where TConsumerDataModel : class
{
    /// <summary>
    /// Map from the consumer data model to the storage model.
    /// </summary>
    /// <param name="dataModel">The consumer data model record to map.</param>
    /// <returns>The mapped result.</returns>
    TStorageModel MapFromDataToStorageModel(TConsumerDataModel dataModel);

    /// <summary>
    /// Map from the storage model to the consumer data model.
    /// </summary>
    /// <param name="storageModel">The storage data model record to map.</param>
    /// <param name="options">The <see cref="GetRecordOptions"/> of the operation that this mapping is needed for.</param>
    /// <returns>The mapped result.</returns>
    TConsumerDataModel MapFromStorageToDataModel(TStorageModel storageModel, GetRecordOptions? options = default);
}
