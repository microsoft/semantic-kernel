// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
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
/// A mapper that maps between the generic semantic kernel data model and the model that the data is stored in in Redis when using hash sets.
/// </summary>
internal class RedisHashSetGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, (string Key, HashEntry[] HashEntries)>
{
    /// <summary>A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;
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
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Redis when using hash sets.
/// </summary>
internal class RedisHashSetGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, (string Key, HashEntry[] HashEntries)>
{
    /// <summary>All the properties from the record definition.</summary>
    private readonly IReadOnlyList<VectorStoreRecordProperty> _properties;
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

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHashSetGenericDataModelMapper"/> class.
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
    /// <param name="vectorStoreRecordDefinition">A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</param>
    public RedisHashSetGenericDataModelMapper(VectorStoreRecordDefinition vectorStoreRecordDefinition)
    {
        Verify.NotNull(vectorStoreRecordDefinition);

        this._vectorStoreRecordDefinition = vectorStoreRecordDefinition;
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
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// <param name="properties">All the properties from the record definition.</param>
    public RedisHashSetGenericDataModelMapper(IReadOnlyList<VectorStoreRecordProperty> properties)
    {
        Verify.NotNull(properties);
        this._properties = properties;
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
    public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        var hashEntries = new List<HashEntry>();

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
        foreach (var property in this._vectorStoreRecordDefinition.Properties)
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
        foreach (var property in this._vectorStoreRecordDefinition.Properties)
=======
        foreach (var property in this._properties)
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
        foreach (var property in this._properties)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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
        foreach (var property in this._vectorStoreRecordDefinition.Properties)
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
        foreach (var property in this._vectorStoreRecordDefinition.Properties)
=======
        foreach (var property in this._properties)
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
        foreach (var property in this._properties)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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
=======

>>>>>>> main
>>>>>>> Stashed changes
=======
=======

>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
