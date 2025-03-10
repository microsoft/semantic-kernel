// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class RecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, IDictionary<string, object?>>
{
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    internal RecordMapper(VectorStoreRecordPropertyReader propertyReader) => this._propertyReader = propertyReader;

    public IDictionary<string, object?> MapFromDataToStorageModel(TRecord dataModel)
    {
        Dictionary<string, object?> map = new(StringComparer.Ordinal);

        map[SqlServerCommandBuilder.GetColumnName(this._propertyReader.KeyProperty)] = this._propertyReader.KeyPropertyInfo.GetValue(dataModel);

        var dataProperties = this._propertyReader.DataProperties;
        var dataPropertiesInfo = this._propertyReader.DataPropertiesInfo;
        for (int i = 0; i < dataProperties.Count; i++)
        {
            object? value = dataPropertiesInfo[i].GetValue(dataModel);
            map[SqlServerCommandBuilder.GetColumnName(dataProperties[i])] = value;
        }
        var vectorProperties = this._propertyReader.VectorProperties;
        var vectorPropertiesInfo = this._propertyReader.VectorPropertiesInfo;
        for (int i = 0; i < vectorProperties.Count; i++)
        {
            // We restrict the vector properties to ReadOnlyMemory<float> so the cast here is safe.
            ReadOnlyMemory<float> floats = (ReadOnlyMemory<float>)vectorPropertiesInfo[i].GetValue(dataModel)!;
            map[SqlServerCommandBuilder.GetColumnName(vectorProperties[i])] = floats;
        }

        return map;
    }

    public TRecord MapFromStorageToDataModel(IDictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        TRecord record = Activator.CreateInstance<TRecord>()!;
        SetValue(storageModel, record, this._propertyReader.KeyPropertyInfo, this._propertyReader.KeyProperty);
        var data = this._propertyReader.DataProperties;
        var dataInfo = this._propertyReader.DataPropertiesInfo;
        for (int i = 0; i < data.Count; i++)
        {
            SetValue(storageModel, record, dataInfo[i], data[i]);
        }

        if (options.IncludeVectors)
        {
            var vector = this._propertyReader.VectorProperties;
            var vectorInfo = this._propertyReader.VectorPropertiesInfo;
            for (int i = 0; i < vector.Count; i++)
            {
                object? value = storageModel[SqlServerCommandBuilder.GetColumnName(vector[i])];
                if (value is not null)
                {
                    if (value is ReadOnlyMemory<float> floats)
                    {
                        vectorInfo[i].SetValue(record, floats);
                    }
                    else
                    {
                        // When deserializing a string to a ReadOnlyMemory<float> fails in SqlDataReaderDictionary,
                        // we store the raw value so the user can handle the error in a custom mapper.
                        throw new VectorStoreRecordMappingException($"Failed to deserialize vector property '{vector[i].DataModelPropertyName}', it contained value '{value}'.");
                    }
                }
            }
        }

        return record;

        static void SetValue(IDictionary<string, object?> storageModel, object record, PropertyInfo propertyInfo, VectorStoreRecordProperty property)
        {
            // If we got here, there should be no column name mismatch (the query would fail).
            object? value = storageModel[SqlServerCommandBuilder.GetColumnName(property)];

            if (value is null)
            {
                // There is no need to call the reflection to set the null,
                // as it's the default value of every .NET reference type field.
                return;
            }

            try
            {
                propertyInfo.SetValue(record, value);
            }
            catch (Exception ex)
            {
                throw new VectorStoreRecordMappingException($"Failed to set value '{value}' on property '{propertyInfo.Name}' of type '{propertyInfo.PropertyType.FullName}'.", ex);
            }
        }
    }
}
