// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class GenericRecordMapper<TKey> : IVectorStoreRecordMapper<VectorStoreGenericDataModel<TKey>, IDictionary<string, object?>>
    where TKey : notnull
{
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    internal GenericRecordMapper(VectorStoreRecordPropertyReader propertyReader) => this._propertyReader = propertyReader;

    public IDictionary<string, object?> MapFromDataToStorageModel(VectorStoreGenericDataModel<TKey> dataModel)
    {
        Dictionary<string, object?> properties = new()
        {
            { SqlServerCommandBuilder.GetColumnName(this._propertyReader.KeyProperty), dataModel.Key }
        };

        foreach (var property in this._propertyReader.DataProperties)
        {
            string name = SqlServerCommandBuilder.GetColumnName(property);
            if (dataModel.Data.TryGetValue(name, out var dataValue))
            {
                properties.Add(name, dataValue);
            }
        }

        // Add vector properties
        if (dataModel.Vectors is not null)
        {
            foreach (var property in this._propertyReader.VectorProperties)
            {
                string name = SqlServerCommandBuilder.GetColumnName(property);
                if (dataModel.Vectors.TryGetValue(name, out var vectorValue))
                {
                    if (vectorValue is ReadOnlyMemory<float> floats)
                    {
                        properties.Add(name, floats);
                    }
                    else if (vectorValue is not null)
                    {
                        throw new VectorStoreRecordMappingException($"Vector property '{name}' contained value of non supported type: '{vectorValue.GetType().FullName}'.");
                    }
                }
            }
        }

        return properties;
    }

    public VectorStoreGenericDataModel<TKey> MapFromStorageToDataModel(IDictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        TKey key;
        var dataProperties = new Dictionary<string, object?>();
        var vectorProperties = new Dictionary<string, object?>();

        if (storageModel.TryGetValue(SqlServerCommandBuilder.GetColumnName(this._propertyReader.KeyProperty), out var keyObject) && keyObject is not null)
        {
            key = (TKey)keyObject;
        }
        else
        {
            throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
        }

        foreach (var property in this._propertyReader.DataProperties)
        {
            string name = SqlServerCommandBuilder.GetColumnName(property);
            if (storageModel.TryGetValue(name, out var dataValue))
            {
                dataProperties.Add(name, dataValue);
            }
        }

        if (options.IncludeVectors)
        {
            foreach (var property in this._propertyReader.VectorProperties)
            {
                string name = SqlServerCommandBuilder.GetColumnName(property);
                if (storageModel.TryGetValue(name, out var vectorValue))
                {
                    vectorProperties.Add(name, vectorValue);
                }
            }
        }

        return new(key) { Data = dataProperties, Vectors = vectorProperties };
    }
}
