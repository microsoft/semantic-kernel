// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Data;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a hashset stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisHashSetVectorStoreRecordMapper<TConsumerDataModel> : IVectorStoreRecordMapper<TConsumerDataModel, (string Key, HashEntry[] HashEntries)>
    where TConsumerDataModel : class
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
        var jsonObject = new JsonObject();

        foreach (var property in this._propertyReader.DataPropertiesInfo)
        {
            var storageName = this._propertyReader.GetStoragePropertyName(property.Name);
            var jsonName = this._propertyReader.GetJsonPropertyName(property.Name);
            var hashEntry = storageModel.HashEntries.FirstOrDefault(x => x.Name == storageName);
            if (hashEntry.Name.HasValue)
            {
                var typeOrNullableType = Nullable.GetUnderlyingType(property.PropertyType) ?? property.PropertyType;
                var convertedValue = Convert.ChangeType(hashEntry.Value, typeOrNullableType);
                jsonObject.Add(jsonName, JsonValue.Create(convertedValue));
            }
        }

        if (options.IncludeVectors)
        {
            foreach (var property in this._propertyReader.VectorPropertiesInfo)
            {
                var storageName = this._propertyReader.GetStoragePropertyName(property.Name);
                var jsonName = this._propertyReader.GetJsonPropertyName(property.Name);

                var hashEntry = storageModel.HashEntries.FirstOrDefault(x => x.Name == storageName);
                if (hashEntry.Name.HasValue)
                {
                    if (property.PropertyType == typeof(ReadOnlyMemory<float>) || property.PropertyType == typeof(ReadOnlyMemory<float>?))
                    {
                        var array = MemoryMarshal.Cast<byte, float>((byte[])hashEntry.Value!).ToArray();
                        jsonObject.Add(jsonName, JsonValue.Create(array));
                    }
                    else if (property.PropertyType == typeof(ReadOnlyMemory<double>) || property.PropertyType == typeof(ReadOnlyMemory<double>?))
                    {
                        var array = MemoryMarshal.Cast<byte, double>((byte[])hashEntry.Value!).ToArray();
                        jsonObject.Add(jsonName, JsonValue.Create(array));
                    }
                    else
                    {
                        throw new VectorStoreRecordMappingException($"Invalid vector type '{property.PropertyType.Name}' found on property '{property.Name}' on provided record of type '{typeof(TConsumerDataModel).FullName}'. Only float and double vectors are supported.");
                    }
                }
            }
        }

        // Check that the key field is not already present in the redis value.
        if (jsonObject.ContainsKey(this._propertyReader.KeyPropertyJsonName))
        {
            throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'. Key property '{this._propertyReader.KeyPropertyJsonName}' is already present on retrieved object.");
        }

        // Since the key is not stored in the redis value, add it back in before deserializing into the data model.
        jsonObject.Add(this._propertyReader.KeyPropertyJsonName, storageModel.Key);

        return JsonSerializer.Deserialize<TConsumerDataModel>(jsonObject)!;
    }
}
