// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
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
    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>The name of the temporary json property that the key field will be serialized / parsed from.</summary>
    private readonly string _keyFieldJsonPropertyName;

    /// <summary>A list of property info objects that point at the data properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly IEnumerable<PropertyInfo> _dataPropertiesInfo;

    /// <summary>A list of property info objects that point at the vector properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly IEnumerable<PropertyInfo> _vectorPropertiesInfo;

    /// <summary>A dictionary that maps from a property name to the configured name that should be used when storing it.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;

    /// <summary>A dictionary that maps from a property name to the configured name that should be used when serializing it to json for data and vector properties.</summary>
    private readonly Dictionary<string, string> _jsonPropertyNames = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHashSetVectorStoreRecordMapper{TConsumerDataModel}"/> class.
    /// </summary>
    /// <param name="vectorStoreRecordDefinition">The record definition that defines the schema of the record type.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the configured name that should be used when storing it.</param>
    public RedisHashSetVectorStoreRecordMapper(
        VectorStoreRecordDefinition vectorStoreRecordDefinition,
        Dictionary<string, string> storagePropertyNames)
    {
        Verify.NotNull(vectorStoreRecordDefinition);
        Verify.NotNull(storagePropertyNames);

        (PropertyInfo keyPropertyInfo, List<PropertyInfo> dataPropertiesInfo, List<PropertyInfo> vectorPropertiesInfo) = VectorStoreRecordPropertyReader.FindProperties(typeof(TConsumerDataModel), vectorStoreRecordDefinition, supportsMultipleVectors: true);

        this._keyPropertyInfo = keyPropertyInfo;
        this._dataPropertiesInfo = dataPropertiesInfo;
        this._vectorPropertiesInfo = vectorPropertiesInfo;
        this._storagePropertyNames = storagePropertyNames;

        this._keyFieldJsonPropertyName = VectorStoreRecordPropertyReader.GetJsonPropertyName(JsonSerializerOptions.Default, keyPropertyInfo);
        foreach (var property in dataPropertiesInfo.Concat(vectorPropertiesInfo))
        {
            this._jsonPropertyNames[property.Name] = VectorStoreRecordPropertyReader.GetJsonPropertyName(JsonSerializerOptions.Default, property);
        }
    }

    /// <inheritdoc />
    public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(TConsumerDataModel dataModel)
    {
        var keyValue = this._keyPropertyInfo.GetValue(dataModel) as string ?? throw new VectorStoreRecordMappingException($"Missing key property {this._keyPropertyInfo.Name} on provided record of type {typeof(TConsumerDataModel).FullName}.");

        var hashEntries = new List<HashEntry>();
        foreach (var property in this._dataPropertiesInfo)
        {
            var storageName = this._storagePropertyNames[property.Name];
            var value = property.GetValue(dataModel);
            hashEntries.Add(new HashEntry(storageName, RedisValue.Unbox(value)));
        }

        foreach (var property in this._vectorPropertiesInfo)
        {
            var storageName = this._storagePropertyNames[property.Name];
            var value = property.GetValue(dataModel);
            if (value is not null)
            {
                // Convert the vector to a byte array and store it in the hash entry.
                // We only support float and double vectors and we do checking in the
                // collection constructor to ensure that the model has no other vector types.
                if (value is ReadOnlyMemory<float> rom)
                {
                    hashEntries.Add(new HashEntry(storageName, ConvertVectorToBytes(rom)));
                }
                else if (value is ReadOnlyMemory<double> rod)
                {
                    hashEntries.Add(new HashEntry(storageName, ConvertVectorToBytes(rod)));
                }
            }
        }

        return (keyValue, hashEntries.ToArray());
    }

    /// <inheritdoc />
    public TConsumerDataModel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
    {
        var jsonObject = new JsonObject();

        foreach (var property in this._dataPropertiesInfo)
        {
            var storageName = this._storagePropertyNames[property.Name];
            var jsonName = this._jsonPropertyNames[property.Name];
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
            foreach (var property in this._vectorPropertiesInfo)
            {
                var storageName = this._storagePropertyNames[property.Name];
                var jsonName = this._jsonPropertyNames[property.Name];

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
        if (jsonObject.ContainsKey(this._keyFieldJsonPropertyName))
        {
            throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'. Key property '{this._keyFieldJsonPropertyName}' is already present on retrieved object.");
        }

        // Since the key is not stored in the redis value, add it back in before deserializing into the data model.
        jsonObject.Add(this._keyFieldJsonPropertyName, storageModel.Key);

        return JsonSerializer.Deserialize<TConsumerDataModel>(jsonObject)!;
    }

    private static byte[] ConvertVectorToBytes(ReadOnlyMemory<float> vector)
    {
        return MemoryMarshal.AsBytes(vector.Span).ToArray();
    }

    private static byte[] ConvertVectorToBytes(ReadOnlyMemory<double> vector)
    {
        return MemoryMarshal.AsBytes(vector.Span).ToArray();
    }
}
