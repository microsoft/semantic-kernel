// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Redis when using hash sets.
/// </summary>
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
internal sealed class RedisHashSetGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, (string Key, HashEntry[] HashEntries)>
#pragma warning restore CS0618
{
    /// <summary>All the properties from the record definition.</summary>
    private readonly IReadOnlyList<VectorStoreRecordProperty> _properties;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHashSetGenericDataModelMapper"/> class.
    /// </summary>
    /// <param name="properties">All the properties from the record definition.</param>
    public RedisHashSetGenericDataModelMapper(IReadOnlyList<VectorStoreRecordProperty> properties)
    {
        Verify.NotNull(properties);
        this._properties = properties;
    }

    /// <inheritdoc />
    public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        var hashEntries = new List<HashEntry>();

        foreach (var property in this._properties)
        {
            var storagePropertyName = property.StoragePropertyName ?? property.DataModelPropertyName;
            var sourceDictionary = property is VectorStoreRecordDataProperty ? dataModel.Data : dataModel.Vectors;

            // Only map properties across that actually exist in the input.
            if (sourceDictionary is null || !sourceDictionary.TryGetValue(property.DataModelPropertyName, out var sourceValue))
            {
                continue;
            }

            // Replicate null if the property exists but is null.
            if (sourceValue is null)
            {
                hashEntries.Add(new HashEntry(storagePropertyName, RedisValue.Null));
                continue;
            }

            // Map data Properties
            if (property is VectorStoreRecordDataProperty dataProperty)
            {
                hashEntries.Add(new HashEntry(storagePropertyName, RedisValue.Unbox(sourceValue)));
            }
            // Map vector properties
            else if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                if (sourceValue is ReadOnlyMemory<float> rom)
                {
                    hashEntries.Add(new HashEntry(storagePropertyName, RedisVectorStoreRecordFieldMapping.ConvertVectorToBytes(rom)));
                }
                else if (sourceValue is ReadOnlyMemory<double> rod)
                {
                    hashEntries.Add(new HashEntry(storagePropertyName, RedisVectorStoreRecordFieldMapping.ConvertVectorToBytes(rod)));
                }
                else
                {
                    throw new VectorStoreRecordMappingException($"Unsupported vector type {sourceValue.GetType().Name} found on property ${vectorProperty.DataModelPropertyName}. Only float and double vectors are supported.");
                }
            }
        }

        return (dataModel.Key, hashEntries.ToArray());
    }

    /// <inheritdoc />
    public VectorStoreGenericDataModel<string> MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
    {
        var dataModel = new VectorStoreGenericDataModel<string>(storageModel.Key);

        foreach (var property in this._properties)
        {
            var storagePropertyName = property.StoragePropertyName ?? property.DataModelPropertyName;
            var targetDictionary = property is VectorStoreRecordDataProperty ? dataModel.Data : dataModel.Vectors;
            var hashEntry = storageModel.HashEntries.FirstOrDefault(x => x.Name == storagePropertyName);

            // Only map properties across that actually exist in the input.
            if (!hashEntry.Name.HasValue)
            {
                continue;
            }

            // Replicate null if the property exists but is null.
            if (hashEntry.Value.IsNull)
            {
                targetDictionary.Add(property.DataModelPropertyName, null);
                continue;
            }

            // Map data Properties
            if (property is VectorStoreRecordDataProperty dataProperty)
            {
                var typeOrNullableType = Nullable.GetUnderlyingType(property.PropertyType) ?? property.PropertyType;
                var convertedValue = Convert.ChangeType(hashEntry.Value, typeOrNullableType);
                dataModel.Data.Add(dataProperty.DataModelPropertyName, convertedValue);
            }

            // Map vector properties
            else if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                if (property.PropertyType == typeof(ReadOnlyMemory<float>) || property.PropertyType == typeof(ReadOnlyMemory<float>?))
                {
                    var array = MemoryMarshal.Cast<byte, float>((byte[])hashEntry.Value!).ToArray();
                    dataModel.Vectors.Add(vectorProperty.DataModelPropertyName, new ReadOnlyMemory<float>(array));
                }
                else if (property.PropertyType == typeof(ReadOnlyMemory<double>) || property.PropertyType == typeof(ReadOnlyMemory<double>?))
                {
                    var array = MemoryMarshal.Cast<byte, double>((byte[])hashEntry.Value!).ToArray();
                    dataModel.Vectors.Add(vectorProperty.DataModelPropertyName, new ReadOnlyMemory<double>(array));
                }
                else
                {
                    throw new VectorStoreRecordMappingException($"Unsupported vector type '{property.PropertyType.Name}' found on property '{property.DataModelPropertyName}'. Only float and double vectors are supported.");
                }
            }
        }

        return dataModel;
    }
}
