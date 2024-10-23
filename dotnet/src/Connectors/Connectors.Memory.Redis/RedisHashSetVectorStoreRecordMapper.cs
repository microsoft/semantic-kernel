// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a hashset stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisHashSetVectorStoreRecordMapper<TConsumerDataModel> : IVectorStoreRecordMapper<TConsumerDataModel, (string Key, HashEntry[] HashEntries)>
{
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHashSetVectorStoreRecordMapper{TConsumerDataModel}"/> class.
    /// </summary>
    /// <param name="propertyReader">A helper to access property information for the current data model and record definition.</param>
    public RedisHashSetVectorStoreRecordMapper(
        VectorStoreRecordPropertyReader propertyReader)
    {
        Verify.NotNull(propertyReader);

        propertyReader.VerifyHasParameterlessConstructor();

        this._propertyReader = propertyReader;
    }

    /// <inheritdoc />
    public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(TConsumerDataModel dataModel)
    {
        var keyValue = this._propertyReader.KeyPropertyInfo.GetValue(dataModel) as string ??
            throw new VectorStoreRecordMappingException($"Missing key property {this._propertyReader.KeyPropertyName} on provided record of type {typeof(TConsumerDataModel).FullName}.");

        var hashEntries = new List<HashEntry>();
        foreach (var property in this._propertyReader.DataPropertiesInfo)
        {
            var storageName = this._propertyReader.GetStoragePropertyName(property.Name);
            var value = property.GetValue(dataModel);
            hashEntries.Add(new HashEntry(storageName, RedisValue.Unbox(value)));
        }

        foreach (var property in this._propertyReader.VectorPropertiesInfo)
        {
            var storageName = this._propertyReader.GetStoragePropertyName(property.Name);
            var value = property.GetValue(dataModel);
            if (value is not null)
            {
                // Convert the vector to a byte array and store it in the hash entry.
                // We only support float and double vectors and we do checking in the
                // collection constructor to ensure that the model has no other vector types.
                if (value is ReadOnlyMemory<float> rom)
                {
                    hashEntries.Add(new HashEntry(storageName, RedisVectorStoreRecordFieldMapping.ConvertVectorToBytes(rom)));
                }
                else if (value is ReadOnlyMemory<double> rod)
                {
                    hashEntries.Add(new HashEntry(storageName, RedisVectorStoreRecordFieldMapping.ConvertVectorToBytes(rod)));
                }
            }
        }

        return (keyValue, hashEntries.ToArray());
    }

    /// <inheritdoc />
    public TConsumerDataModel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
    {
        var hashEntriesDictionary = storageModel.HashEntries.ToDictionary(x => (string)x.Name!, x => x.Value);

        // Construct the output record.
        var outputRecord = (TConsumerDataModel)this._propertyReader.ParameterLessConstructorInfo.Invoke(null);

        // Set Key.
        this._propertyReader.KeyPropertyInfo.SetValue(outputRecord, storageModel.Key);

        // Set each vector property if embeddings should be returned.
        if (options?.IncludeVectors is true)
        {
            VectorStoreRecordMapping.SetValuesOnProperties(
                outputRecord,
                this._propertyReader.VectorPropertiesInfo,
                this._propertyReader.StoragePropertyNamesMap,
                hashEntriesDictionary,
                (RedisValue vector, Type targetType) =>
                {
                    if (targetType == typeof(ReadOnlyMemory<float>) || targetType == typeof(ReadOnlyMemory<float>?))
                    {
                        var array = MemoryMarshal.Cast<byte, float>((byte[])vector!).ToArray();
                        return new ReadOnlyMemory<float>(array);
                    }
                    else if (targetType == typeof(ReadOnlyMemory<double>) || targetType == typeof(ReadOnlyMemory<double>?))
                    {
                        var array = MemoryMarshal.Cast<byte, double>((byte[])vector!).ToArray();
                        return new ReadOnlyMemory<double>(array);
                    }
                    else
                    {
                        throw new VectorStoreRecordMappingException($"Unsupported vector type '{targetType}'. Only float and double vectors are supported.");
                    }
                });
        }

        // Set each data property.
        VectorStoreRecordMapping.SetValuesOnProperties(
            outputRecord,
            this._propertyReader.DataPropertiesInfo,
            this._propertyReader.StoragePropertyNamesMap,
            hashEntriesDictionary,
            (RedisValue hashValue, Type targetType) =>
            {
                var typeOrNullableType = Nullable.GetUnderlyingType(targetType) ?? targetType;
                return Convert.ChangeType(hashValue, typeOrNullableType);
            });

        return outputRecord;
    }
}
