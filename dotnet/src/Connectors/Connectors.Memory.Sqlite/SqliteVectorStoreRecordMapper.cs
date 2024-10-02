// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.InteropServices;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Class for mapping between a dictionary and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class SqliteVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>>
    where TRecord : class
{
    /// <summary>A dictionary that maps from a property name to the storage name.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;

    /// <summary>The public parameterless constructor for the current data model.</summary>
    private readonly ConstructorInfo _constructorInfo;

    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>A list of property info objects that point at the data properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly List<PropertyInfo> _dataPropertiesInfo;

    /// <summary>A list of property info objects that point at the vector properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly List<PropertyInfo> _vectorPropertiesInfo;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreRecordMapper{TRecord}"/> class.
    /// </summary>
    /// <param name="vectorStoreRecordDefinition">A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name.</param>
    public SqliteVectorStoreRecordMapper(
        VectorStoreRecordDefinition vectorStoreRecordDefinition,
        Dictionary<string, string> storagePropertyNames)
    {
        Verify.NotNull(vectorStoreRecordDefinition);
        Verify.NotNull(storagePropertyNames);

        this._constructorInfo = VectorStoreRecordPropertyReader.GetParameterlessConstructor(typeof(TRecord));

        var (keyPropertyInfo, dataPropertiesInfo, vectorPropertiesInfo) = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), vectorStoreRecordDefinition, supportsMultipleVectors: true);

        this._keyPropertyInfo = keyPropertyInfo;
        this._dataPropertiesInfo = dataPropertiesInfo;
        this._vectorPropertiesInfo = vectorPropertiesInfo;
        this._storagePropertyNames = storagePropertyNames;
    }

    public Dictionary<string, object?> MapFromDataToStorageModel(TRecord dataModel)
    {
        var properties = new Dictionary<string, object?>
        {
            // Add key property
            { this._storagePropertyNames[this._keyPropertyInfo.Name], this._keyPropertyInfo.GetValue(dataModel) }
        };

        // Add data properties
        foreach (var property in this._dataPropertiesInfo)
        {
            properties.Add(this._storagePropertyNames[property.Name], property.GetValue(dataModel));
        }

        // Add vector properties
        foreach (var property in this._vectorPropertiesInfo)
        {
            object? result = null;
            var propertyValue = property.GetValue(dataModel);

            if (propertyValue is not null)
            {
                var vector = (ReadOnlyMemory<float>)propertyValue;
                var serializedVector = $"[{string.Join(", ", vector.ToArray())}]";
                result = serializedVector;
            }

            properties.Add(this._storagePropertyNames[property.Name], result);
        }

        return properties;
    }

    public TRecord MapFromStorageToDataModel(Dictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        var record = (TRecord)this._constructorInfo.Invoke(null);

        // Set key.
        var keyPropertyInfoWithValue = new KeyValuePair<PropertyInfo, object?>(
            this._keyPropertyInfo,
            storageModel[this._storagePropertyNames[this._keyPropertyInfo.Name]]);

        VectorStoreRecordMapping.SetPropertiesOnRecord(record, [keyPropertyInfoWithValue]);

        // Process data properties.
        var dataPropertiesInfoWithValues = VectorStoreRecordMapping.BuildPropertiesInfoWithValues(
            this._dataPropertiesInfo,
            this._storagePropertyNames,
            storageModel);

        VectorStoreRecordMapping.SetPropertiesOnRecord(record, dataPropertiesInfoWithValues);

        if (options.IncludeVectors)
        {
            // Process vector properties.
            var vectorPropertiesInfoWithValues = VectorStoreRecordMapping.BuildPropertiesInfoWithValues(
                this._vectorPropertiesInfo,
                this._storagePropertyNames,
                storageModel,
                (object? vector, Type targetType) =>
                {
                    var vectorBytes = vector as byte[];

                    if (vectorBytes is null)
                    {
                        return null;
                    }

                    var vectorArray = MemoryMarshal.Cast<byte, float>(vectorBytes).ToArray();
                    return new ReadOnlyMemory<float>(vectorArray);
                });

            VectorStoreRecordMapping.SetPropertiesOnRecord(record, vectorPropertiesInfoWithValues);
        }

        return record;
    }
}
