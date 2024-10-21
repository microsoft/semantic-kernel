<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

using System;
using System.Collections.Generic;
using System.Linq;
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Nodes;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
using System.Runtime.InteropServices;
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
=======
using System.Runtime.InteropServices;
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
using System.Runtime.InteropServices;
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
using System.Runtime.InteropServices;
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
using System.Runtime.InteropServices;
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
using System.Runtime.InteropServices;
>>>>>>> main
>>>>>>> Stashed changes
=======
using System.Runtime.InteropServices;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using System.Runtime.InteropServices;
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
using System.Runtime.InteropServices;
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< div
=======
using System.Runtime.InteropServices;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
using Microsoft.SemanticKernel.Data;
=======
using Microsoft.Extensions.VectorData;
>>>>>>> upstream/main
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a hashset stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisHashSetVectorStoreRecordMapper<TConsumerDataModel> : IVectorStoreRecordMapper<TConsumerDataModel, (string Key, HashEntry[] HashEntries)>
{
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHashSetVectorStoreRecordMapper{TConsumerDataModel}"/> class.
    /// </summary>
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
    /// <param name="propertyReader">A helper to access property information for the current data model and record definition.</param>
    public RedisHashSetVectorStoreRecordMapper(
        VectorStoreRecordPropertyReader propertyReader)
    {
        Verify.NotNull(propertyReader);

        propertyReader.VerifyHasParameterlessConstructor();

        this._propertyReader = propertyReader;
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    }

    /// <inheritdoc />
    public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(TConsumerDataModel dataModel)
    {
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        var keyValue = this._keyPropertyInfo.GetValue(dataModel) as string ?? throw new VectorStoreRecordMappingException($"Missing key property {this._keyPropertyInfo.Name} on provided record of type {typeof(TConsumerDataModel).FullName}.");

        var hashEntries = new List<HashEntry>();
        foreach (var property in this._dataPropertiesInfo)
        {
            var storageName = this._storagePropertyNames[property.Name];
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        var keyValue = this._propertyReader.KeyPropertyInfo.GetValue(dataModel) as string ??
            throw new VectorStoreRecordMappingException($"Missing key property {this._propertyReader.KeyPropertyName} on provided record of type {typeof(TConsumerDataModel).FullName}.");

        var hashEntries = new List<HashEntry>();
        foreach (var property in this._propertyReader.DataPropertiesInfo)
        {
            var storageName = this._propertyReader.GetStoragePropertyName(property.Name);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
            var value = property.GetValue(dataModel);
            hashEntries.Add(new HashEntry(storageName, RedisValue.Unbox(value)));
        }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        foreach (var property in this._vectorPropertiesInfo)
        {
            var storageName = this._storagePropertyNames[property.Name];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        foreach (var property in this._vectorPropertiesInfo)
        {
            var storageName = this._storagePropertyNames[property.Name];
=======
        foreach (var property in this._propertyReader.VectorPropertiesInfo)
        {
            var storageName = this._propertyReader.GetStoragePropertyName(property.Name);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        foreach (var property in this._propertyReader.VectorPropertiesInfo)
        {
            var storageName = this._propertyReader.GetStoragePropertyName(property.Name);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
                    hashEntries.Add(new HashEntry(storageName, ConvertVectorToBytes(rom)));
                }
                else if (value is ReadOnlyMemory<double> rod)
                {
                    hashEntries.Add(new HashEntry(storageName, ConvertVectorToBytes(rod)));
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                }
            }
        }

        return (keyValue, hashEntries.ToArray());
    }

    /// <inheritdoc />
    public TConsumerDataModel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
    {
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
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

    private static byte[] ConvertVectorToBytes(ReadOnlyMemory<float> vector)
    {
        return MemoryMarshal.AsBytes(vector.Span).ToArray();
    }

    private static byte[] ConvertVectorToBytes(ReadOnlyMemory<double> vector)
    {
        return MemoryMarshal.AsBytes(vector.Span).ToArray();
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    }
}
